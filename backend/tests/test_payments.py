import asyncio
from typing import Any

import httpx
import pytest
from sqlalchemy import func, select, update

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Food, Payment, PaymentStatus
from app.services.orders import expire_stale_orders
from app.utils.time import utcnow
from tests.conftest import place_order, stock_of


async def _order(client: httpx.AsyncClient, menu: dict[str, Food], qty: int = 2) -> dict[str, Any]:
    body = (await place_order(client, [(menu["chicken_rice"], qty), (menu["milk_tea"], 1)])).json()
    return {
        "order_id": body["order"]["id"],
        "payment_id": body["payment"]["id"],
        "headers": {"X-Order-Token": body["access_token"]},
    }


async def _confirm(client: httpx.AsyncClient, o: dict[str, Any]) -> httpx.Response:
    return await client.post(
        "/payments/demo/confirm",
        json={"order_id": o["order_id"], "payment_id": o["payment_id"]},
        headers=o["headers"],
    )


async def test_demo_payment_confirms_the_order(
    menu: dict[str, Food], client: httpx.AsyncClient
) -> None:
    o = await _order(client, menu)
    response = await _confirm(client, o)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "paid"
    assert body["order_status"] == "confirmed"
    assert body["already_confirmed"] is False
    assert body["transaction_reference"].startswith("DEMO-")

    order = (await client.get(f"/orders/{o['order_id']}", headers=o["headers"])).json()
    assert order["status"] == "confirmed"
    assert order["payment"]["status"] == "paid"
    status = (await client.get(f"/payments/{o['payment_id']}/status", headers=o["headers"])).json()
    assert status["status"] == "paid"


async def test_repeated_confirmation_is_idempotent(
    menu: dict[str, Food], client: httpx.AsyncClient
) -> None:
    o = await _order(client, menu)
    first = (await _confirm(client, o)).json()
    second = await _confirm(client, o)
    assert second.status_code == 200
    assert second.json()["already_confirmed"] is True
    assert second.json()["transaction_reference"] == first["transaction_reference"]
    assert second.json()["paid_at"] == first["paid_at"]


async def test_concurrent_confirmations_charge_once(
    menu: dict[str, Food], client: httpx.AsyncClient
) -> None:
    o = await _order(client, menu)
    results = await asyncio.gather(*[_confirm(client, o) for _ in range(5)])
    assert all(r.status_code == 200 for r in results)
    assert [r.json()["already_confirmed"] for r in results].count(False) == 1
    assert len({r.json()["transaction_reference"] for r in results}) == 1
    async with SessionLocal() as session:
        paid = await session.scalar(
            select(func.count()).where(Payment.status == PaymentStatus.PAID)
        )
    assert paid == 1


async def test_payment_must_belong_to_the_order(
    menu: dict[str, Food], client: httpx.AsyncClient
) -> None:
    mine = await _order(client, menu, qty=1)
    theirs = await _order(client, menu, qty=1)
    # My valid token + someone else's payment id.
    mismatched = await client.post(
        "/payments/demo/confirm",
        json={"order_id": mine["order_id"], "payment_id": theirs["payment_id"]},
        headers=mine["headers"],
    )
    assert mismatched.status_code == 404
    # Someone else's order with my token.
    stolen = await client.post(
        "/payments/demo/confirm",
        json={"order_id": theirs["order_id"], "payment_id": theirs["payment_id"]},
        headers=mine["headers"],
    )
    assert stolen.status_code == 404
    # No token at all.
    anonymous = await client.post(
        "/payments/demo/confirm",
        json={"order_id": theirs["order_id"], "payment_id": theirs["payment_id"]},
    )
    assert anonymous.status_code == 404
    status = (await client.get(f"/orders/{theirs['order_id']}", headers=theirs["headers"])).json()
    assert status["status"] == "pending_payment"


async def test_demo_confirmation_disabled_outside_demo_mode(
    menu: dict[str, Food], client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    o = await _order(client, menu)
    monkeypatch.setattr(settings, "demo_payments_enabled", False)
    response = await _confirm(client, o)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "DEMO_DISABLED"


async def _expire(payment_id: str) -> None:
    async with SessionLocal() as session:
        await session.execute(
            update(Payment).where(Payment.id == payment_id).values(expires_at=func.now())
        )
        await session.commit()


async def test_expired_payment_cancels_order_and_releases_stock(
    menu: dict[str, Food], client: httpx.AsyncClient
) -> None:
    o = await _order(client, menu, qty=4)
    assert await stock_of(menu["chicken_rice"]) == 6
    await _expire(o["payment_id"])

    response = await _confirm(client, o)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PAYMENT_EXPIRED"
    order = (await client.get(f"/orders/{o['order_id']}", headers=o["headers"])).json()
    assert order["status"] == "cancelled"
    assert order["payment"]["status"] == "expired"
    assert await stock_of(menu["chicken_rice"]) == 10
    # Retrying never resurrects the order or double-releases stock.
    assert (await _confirm(client, o)).status_code == 409
    assert await stock_of(menu["chicken_rice"]) == 10


async def test_background_sweep_expires_unpaid_orders(
    menu: dict[str, Food], client: httpx.AsyncClient
) -> None:
    o = await _order(client, menu, qty=3)
    await _expire(o["payment_id"])
    async with SessionLocal() as session:
        assert await expire_stale_orders(session) == 1
        assert await expire_stale_orders(session) == 0
    assert await stock_of(menu["chicken_rice"]) == 10


async def test_create_checkout_is_idempotent(
    menu: dict[str, Food], client: httpx.AsyncClient
) -> None:
    o = await _order(client, menu)
    a = await client.post(
        "/payments/demo/create", json={"order_id": o["order_id"]}, headers=o["headers"]
    )
    b = await client.post(
        "/payments/demo/create", json={"order_id": o["order_id"]}, headers=o["headers"]
    )
    assert a.status_code == b.status_code == 200
    assert a.json()["id"] == b.json()["id"] == o["payment_id"]
    assert a.json()["is_demo"] is True
    unauthorized = await client.post("/payments/demo/create", json={"order_id": o["order_id"]})
    assert unauthorized.status_code == 404


async def test_paid_at_is_recorded(menu: dict[str, Food], client: httpx.AsyncClient) -> None:
    o = await _order(client, menu)
    before = utcnow()
    await _confirm(client, o)
    async with SessionLocal() as session:
        payment = await session.get(Payment, o["payment_id"])
    assert payment is not None and payment.paid_at is not None and payment.paid_at >= before
