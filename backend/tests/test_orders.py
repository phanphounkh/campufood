import asyncio
from datetime import datetime, timedelta

import httpx
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Food, InventoryMovement, InventoryReason
from tests.conftest import TZ, pickup_time, place_order, stock_of


async def test_order_total_is_computed_by_the_server(
    menu: dict[str, Food], client: httpx.AsyncClient
) -> None:
    response = await place_order(
        client,
        [(menu["chicken_rice"], 2), (menu["milk_tea"], 1)],
        # Clients cannot inject prices: unknown fields like these are ignored.
        total="0.01",
        unit_price="0.01",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    order = body["order"]
    assert order["order_number"] == "CE-1001"
    assert order["status"] == "pending_payment"
    assert order["subtotal"] == "3.75" and order["total"] == "3.75"
    lines = {i["food_name_snapshot"]: i for i in order["items"]}
    assert lines["Chicken Rice"]["unit_price"] == "1.50"
    assert lines["Chicken Rice"]["line_total"] == "3.00"
    assert lines["Iced Milk Tea"]["line_total"] == "0.75"
    assert order["customer_phone"] == "012345678"
    assert body["payment"]["status"] == "pending"
    assert body["payment"]["amount"] == "3.75"
    assert body["payment"]["qr_payload"].startswith("CAMPUSEATS-DEMO|NOT-A-REAL-PAYMENT")
    assert len(body["access_token"]) >= 40


async def test_duplicate_lines_are_merged(menu: dict[str, Food], client: httpx.AsyncClient) -> None:
    response = await place_order(client, [(menu["milk_tea"], 1), (menu["milk_tea"], 2)])
    items = response.json()["order"]["items"]
    assert len(items) == 1 and items[0]["quantity"] == 3
    assert response.json()["order"]["total"] == "2.25"


async def test_stale_cart_total_is_rejected(
    menu: dict[str, Food], client: httpx.AsyncClient
) -> None:
    response = await place_order(client, [(menu["chicken_rice"], 1)], expected_total="1.25")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PRICE_CHANGED"
    assert response.json()["error"]["details"]["actual_total"] == "1.50"
    assert await stock_of(menu["chicken_rice"]) == 10  # nothing reserved
    ok = await place_order(client, [(menu["chicken_rice"], 1)], expected_total="1.50")
    assert ok.status_code == 201


async def test_unavailable_items_are_rejected(
    menu: dict[str, Food], client: httpx.AsyncClient
) -> None:
    for food, qty, reason in [
        (menu["sold_out"], 1, "insufficient_stock"),
        (menu["unavailable"], 1, "unavailable"),
        (menu["fried_rice"], 4, "insufficient_stock"),
    ]:
        response = await place_order(client, [(food, qty)])
        assert response.status_code == 409
        assert response.json()["error"]["details"][0]["reason"] == reason
    missing = await client.post(
        "/orders",
        json={
            "customer_name": "A B",
            "customer_phone": "012345678",
            "pickup_time": pickup_time(),
            "items": [{"food_id": 9999, "quantity": 1}],
        },
    )
    assert missing.status_code == 409


async def test_order_validation(menu: dict[str, Food], client: httpx.AsyncClient) -> None:
    item = [(menu["chicken_rice"], 1)]
    assert (await place_order(client, [])).status_code == 422
    assert (await place_order(client, [(menu["chicken_rice"], 0)])).status_code == 422
    assert (await place_order(client, [(menu["chicken_rice"], 21)])).status_code == 422
    assert (await place_order(client, item, customer_name=" ")).status_code == 422
    assert (await place_order(client, item, customer_phone="call me")).status_code == 422
    assert (await place_order(client, item, customer_phone="123")).status_code == 422
    naive = datetime.now().replace(microsecond=0).isoformat()
    assert (await place_order(client, item, pickup_time=naive)).status_code == 422


async def test_pickup_time_rules(menu: dict[str, Food], client: httpx.AsyncClient) -> None:
    item = [(menu["chicken_rice"], 1)]
    past = (datetime.now(TZ) - timedelta(hours=1)).isoformat()
    too_far = pickup_time(days=10)
    after_hours = pickup_time(hour=22)
    for value in (past, too_far, after_hours):
        response = await place_order(client, item, pickup_time=value)
        assert response.status_code == 400, value
        assert response.json()["error"]["code"] == "INVALID_PICKUP_TIME"


async def test_store_can_stop_taking_orders(
    menu: dict[str, Food], admin_client: httpx.AsyncClient, client: httpx.AsyncClient
) -> None:
    await admin_client.patch("/admin/settings", json={"accepting_orders": False})
    response = await place_order(client, [(menu["chicken_rice"], 1)])
    assert response.status_code == 409 and response.json()["error"]["code"] == "STORE_CLOSED"


async def test_stock_is_reserved_with_a_ledger_entry(
    menu: dict[str, Food], client: httpx.AsyncClient
) -> None:
    response = await place_order(client, [(menu["chicken_rice"], 4)])
    order_id = response.json()["order"]["id"]
    assert await stock_of(menu["chicken_rice"]) == 6
    async with SessionLocal() as session:
        movements = (
            await session.scalars(
                select(InventoryMovement).where(
                    InventoryMovement.reason == InventoryReason.ORDER_RESERVED
                )
            )
        ).all()
    assert [(str(m.order_id), m.quantity_change) for m in movements] == [(order_id, -4)]


async def test_concurrent_orders_cannot_oversell(
    menu: dict[str, Food], client: httpx.AsyncClient
) -> None:
    """Fried Rice has 3 in stock. Eight students try to buy one each at the same moment."""
    results = await asyncio.gather(
        *[place_order(client, [(menu["fried_rice"], 1)]) for _ in range(8)]
    )
    codes = sorted(r.status_code for r in results)
    assert codes.count(201) == 3
    assert codes.count(409) == 5
    assert await stock_of(menu["fried_rice"]) == 0


async def test_guest_order_access_requires_the_secret_token(
    menu: dict[str, Food], client: httpx.AsyncClient, staff_client: httpx.AsyncClient
) -> None:
    created = (await place_order(client, [(menu["chicken_rice"], 1)])).json()
    order_id, token = created["order"]["id"], created["access_token"]

    assert (await client.get(f"/orders/{order_id}")).status_code == 404
    assert (
        await client.get(f"/orders/{order_id}", headers={"X-Order-Token": "guess"})
    ).status_code == 404
    other = (await place_order(client, [(menu["milk_tea"], 1)])).json()
    cross = await client.get(
        f"/orders/{order_id}", headers={"X-Order-Token": other["access_token"]}
    )
    assert cross.status_code == 404

    mine = await client.get(f"/orders/{order_id}", headers={"X-Order-Token": token})
    assert mine.status_code == 200 and mine.json()["id"] == order_id
    assert (await staff_client.get(f"/orders/{order_id}")).status_code == 200


async def test_logged_in_customer_sees_own_history(
    menu: dict[str, Food], customer_client: httpx.AsyncClient, client: httpx.AsyncClient
) -> None:
    mine = (await place_order(customer_client, [(menu["chicken_rice"], 1)])).json()["order"]
    (await place_order(client, [(menu["milk_tea"], 1)]))  # someone else's guest order
    history = (await customer_client.get("/orders/mine")).json()
    assert [o["id"] for o in history["items"]] == [mine["id"]]
    assert (await customer_client.get(f"/orders/{mine['id']}")).status_code == 200
