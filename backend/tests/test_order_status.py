from typing import Any

import httpx
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models import Food, InventoryMovement, InventoryReason
from tests.conftest import place_order, stock_of


async def _paid_order(client: httpx.AsyncClient, food: Food, qty: int = 2) -> dict[str, Any]:
    body = (await place_order(client, [(food, qty)])).json()
    headers = {"X-Order-Token": body["access_token"]}
    await client.post(
        "/payments/demo/confirm",
        json={"order_id": body["order"]["id"], "payment_id": body["payment"]["id"]},
        headers=headers,
    )
    return {"id": body["order"]["id"], "headers": headers}


async def _set(
    c: httpx.AsyncClient, order_id: str, status: str, reason: str | None = None
) -> httpx.Response:
    return await c.patch(f"/orders/{order_id}/status", json={"status": status, "reason": reason})


async def test_full_kitchen_workflow(
    menu: dict[str, Food], client: httpx.AsyncClient, staff_client: httpx.AsyncClient
) -> None:
    order = await _paid_order(client, menu["chicken_rice"])
    for status in ("preparing", "ready", "completed"):
        response = await _set(staff_client, order["id"], status)
        assert response.status_code == 200, response.text
        assert response.json()["status"] == status
    tracked = (await client.get(f"/orders/{order['id']}", headers=order["headers"])).json()
    assert tracked["status"] == "completed"


async def test_invalid_transitions_are_rejected(
    menu: dict[str, Food], client: httpx.AsyncClient, staff_client: httpx.AsyncClient
) -> None:
    unpaid = (await place_order(client, [(menu["chicken_rice"], 1)])).json()["order"]
    for target in ("confirmed", "preparing", "ready", "completed"):
        response = await _set(staff_client, unpaid["id"], target)
        assert response.status_code == 409, target
        assert response.json()["error"]["code"] == "INVALID_TRANSITION"

    paid = await _paid_order(client, menu["milk_tea"])
    assert (await _set(staff_client, paid["id"], "completed")).status_code == 409  # skips steps
    assert (await _set(staff_client, paid["id"], "preparing")).status_code == 200
    assert (await _set(staff_client, paid["id"], "preparing")).status_code == 200  # idempotent
    assert (await _set(staff_client, paid["id"], "confirmed")).status_code == 409  # no going back


async def test_cancel_requires_a_reason(
    menu: dict[str, Food], client: httpx.AsyncClient, staff_client: httpx.AsyncClient
) -> None:
    order = await _paid_order(client, menu["chicken_rice"])
    response = await _set(staff_client, order["id"], "cancelled")
    assert response.status_code == 422


async def test_cancelling_a_paid_order_refunds_and_restores_stock_once(
    menu: dict[str, Food], client: httpx.AsyncClient, staff_client: httpx.AsyncClient
) -> None:
    food = menu["chicken_rice"]
    order = await _paid_order(client, food, qty=3)
    assert await stock_of(food) == 7
    await _set(staff_client, order["id"], "preparing")

    response = await _set(staff_client, order["id"], "cancelled", "Ran out of chicken")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "cancelled"
    assert body["cancel_reason"] == "Ran out of chicken"
    assert body["payment"]["status"] == "refunded"
    assert await stock_of(food) == 10

    # Cancelling again (double click, retry) changes nothing.
    again = await _set(staff_client, order["id"], "cancelled", "again")
    assert again.status_code == 200
    assert await stock_of(food) == 10
    async with SessionLocal() as session:
        releases = await session.scalar(
            select(func.count()).where(InventoryMovement.reason == InventoryReason.ORDER_RELEASED)
        )
    assert releases == 1
    # Completed/cancelled orders are final.
    assert (await _set(staff_client, order["id"], "preparing")).status_code == 409


async def test_customer_can_cancel_only_unpaid_orders(
    menu: dict[str, Food], client: httpx.AsyncClient
) -> None:
    body = (await place_order(client, [(menu["chicken_rice"], 2)])).json()
    headers = {"X-Order-Token": body["access_token"]}
    assert (await client.post(f"/orders/{body['order']['id']}/cancel")).status_code == 404
    cancelled = await client.post(f"/orders/{body['order']['id']}/cancel", headers=headers)
    assert cancelled.status_code == 200 and cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["payment"]["status"] == "cancelled"
    assert await stock_of(menu["chicken_rice"]) == 10

    paid = await _paid_order(client, menu["milk_tea"])
    refused = await client.post(f"/orders/{paid['id']}/cancel", headers=paid["headers"])
    assert refused.status_code == 409


async def test_admin_order_list_filters(
    menu: dict[str, Food], client: httpx.AsyncClient, admin_client: httpx.AsyncClient
) -> None:
    await place_order(client, [(menu["chicken_rice"], 1)], customer_name="Dara Kim")
    paid = await _paid_order(client, menu["milk_tea"])
    confirmed = (await admin_client.get("/admin/orders", params={"status": "confirmed"})).json()
    assert [o["id"] for o in confirmed["items"]] == [paid["id"]]
    by_name = (await admin_client.get("/admin/orders", params={"search": "dara"})).json()
    assert by_name["total"] == 1
    by_number = (await admin_client.get("/admin/orders", params={"search": "1001"})).json()
    assert by_number["items"][0]["order_number"] == "CE-1001"
    summary = (await admin_client.get("/admin/orders-summary")).json()
    assert summary["pending_payment"] == 1 and summary["confirmed"] == 1 and summary["all"] == 2
