"""Inventory, dashboard, reports, settings and uploads."""

import io

import httpx
from PIL import Image

from app.core.config import settings
from app.models import Food
from tests.conftest import place_order, stock_of


async def _paid(client: httpx.AsyncClient, items: list[tuple[Food, int]]) -> str:
    body = (await place_order(client, items)).json()
    await client.post(
        "/payments/demo/confirm",
        json={"order_id": body["order"]["id"], "payment_id": body["payment"]["id"]},
        headers={"X-Order-Token": body["access_token"]},
    )
    return body["order"]["id"]


async def test_inventory_adjustments(
    menu: dict[str, Food], staff_client: httpx.AsyncClient
) -> None:
    food = menu["fried_rice"]
    restocked = await staff_client.patch(
        f"/admin/inventory/{food.id}", json={"mode": "adjust", "quantity": 12, "reason": "restock"}
    )
    assert restocked.status_code == 200 and restocked.json()["stock_quantity"] == 15
    counted = await staff_client.patch(
        f"/admin/inventory/{food.id}",
        json={"mode": "set", "quantity": 9, "reason": "manual_adjustment", "note": "Stock count"},
    )
    assert counted.json()["stock_quantity"] == 9
    negative = await staff_client.patch(f"/admin/inventory/{food.id}", json={"quantity": -50})
    assert negative.status_code == 400
    assert await stock_of(food) == 9

    hidden = await staff_client.patch(
        f"/admin/inventory/{food.id}", json={"quantity": 0, "is_available": False}
    )
    assert hidden.json()["is_available"] is False

    movements = (
        await staff_client.get("/admin/inventory/movements", params={"food_id": food.id})
    ).json()
    assert [m["quantity_change"] for m in movements["items"]][:2] == [-6, 12]

    low = (await staff_client.get("/admin/inventory", params={"low_only": True})).json()
    assert {i["name_en"] for i in low} >= {"Pork Rice", "Fried Rice"}


async def test_dashboard_counts_only_successful_payments(
    menu: dict[str, Food], client: httpx.AsyncClient, admin_client: httpx.AsyncClient
) -> None:
    await _paid(client, [(menu["chicken_rice"], 2), (menu["milk_tea"], 1)])  # 3.75
    await _paid(client, [(menu["chicken_rice"], 1)])  # 1.50
    await place_order(client, [(menu["milk_tea"], 4)])  # unpaid: not revenue

    dash = (await admin_client.get("/admin/dashboard")).json()
    assert dash["total_orders"]["value"] == 2
    assert dash["revenue"]["value"] == "5.25"
    assert dash["average_order_value"]["value"] == "2.63"
    assert dash["pending_orders"] == 2
    assert dash["awaiting_payment"] == 1
    assert dash["popular_items"][0]["name_en"] == "Chicken Rice"
    assert dash["popular_items"][0]["quantity"] == 3
    statuses = {s["status"]: s["count"] for s in dash["orders_by_status"]}
    assert statuses["confirmed"] == 2 and statuses["pending_payment"] == 1
    assert len(dash["recent_orders"]) == 3


async def test_report_separates_gross_refunds_and_net(
    menu: dict[str, Food], client: httpx.AsyncClient, admin_client: httpx.AsyncClient
) -> None:
    await _paid(client, [(menu["chicken_rice"], 2)])  # 3.00
    refunded = await _paid(client, [(menu["milk_tea"], 2)])  # 1.50, later refunded
    await admin_client.patch(
        f"/orders/{refunded}/status", json={"status": "cancelled", "reason": "Customer left"}
    )

    report = (await admin_client.get("/admin/reports", params={"granularity": "day"})).json()
    totals = report["totals"]
    assert totals["gross_sales"] == "4.50"
    assert totals["refunds"] == "1.50"
    assert totals["net_revenue"] == "3.00"
    assert totals["orders"] == 2
    assert totals["cancelled_orders"] == 1
    assert totals["refunded_orders"] == 1
    assert totals["items_sold"] == 2  # refunded items are not counted as sold
    assert report["best_sellers"][0]["name_en"] == "Chicken Rice"
    assert len(report["periods"]) == 30

    dash = (await admin_client.get("/admin/dashboard")).json()
    assert dash["revenue"]["value"] == "3.00"

    csv_response = await admin_client.get("/admin/reports/export")
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    assert "attachment" in csv_response.headers["content-disposition"]
    text = csv_response.text
    assert "Net revenue (USD)" in text and "TOTAL,2,2,4.50,1.50,3.00,1" in text


async def test_report_range_validation(admin_client: httpx.AsyncClient) -> None:
    bad = await admin_client.get(
        "/admin/reports", params={"date_from": "2026-05-01", "date_to": "2026-04-01"}
    )
    assert bad.status_code == 400
    monthly = await admin_client.get(
        "/admin/reports",
        params={"date_from": "2026-01-01", "date_to": "2026-06-30", "granularity": "month"},
    )
    assert [p["period"] for p in monthly.json()["periods"]] == [
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
    ]


async def test_settings(admin_client: httpx.AsyncClient, client: httpx.AsyncClient) -> None:
    updated = await admin_client.patch(
        "/admin/settings", json={"store_name": "Campus Canteen", "opening_time": "06:30"}
    )
    assert updated.status_code == 200 and updated.json()["store_name"] == "Campus Canteen"
    public = (await client.get("/settings")).json()
    assert public["store_name"] == "Campus Canteen"
    assert public["opening_time"] == "06:30"
    assert public["demo_payments_enabled"] is True
    invalid = await admin_client.patch("/admin/settings", json={"closing_time": "05:00"})
    assert invalid.status_code == 422


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (40, 30), (100, 37, 216)).save(buf, format="PNG")
    return buf.getvalue()


async def test_image_upload_is_validated_and_reencoded(admin_client: httpx.AsyncClient) -> None:
    response = await admin_client.post(
        "/admin/uploads/images", files={"file": ("../../evil name.png", _png_bytes(), "image/png")}
    )
    assert response.status_code == 201, response.text
    url = response.json()["url"]
    assert url.startswith("/media/foods/") and url.endswith(".webp")
    assert "evil" not in url
    stored = settings.media_root / "foods" / url.rsplit("/", 1)[1]
    assert stored.exists()
    with Image.open(stored) as img:
        assert img.format == "WEBP"

    fake = await admin_client.post(
        "/admin/uploads/images",
        files={"file": ("photo.png", b"<?php echo 'hi'; ?>", "image/png")},
    )
    assert fake.status_code == 415

    big = await admin_client.post(
        "/admin/uploads/images",
        files={"file": ("big.png", b"0" * (settings.max_upload_bytes + 10), "image/png")},
    )
    assert big.status_code == 413


async def test_customers_aggregate_by_phone(
    menu: dict[str, Food], client: httpx.AsyncClient, admin_client: httpx.AsyncClient
) -> None:
    await _paid(client, [(menu["chicken_rice"], 1)])
    await _paid(client, [(menu["milk_tea"], 2)])
    await place_order(
        client, [(menu["milk_tea"], 1)], customer_name="Bopha Seng", customer_phone="099 111 222"
    )
    customers = (await admin_client.get("/admin/customers")).json()
    assert customers["total"] == 2
    sokha = next(c for c in customers["items"] if c["customer_phone"] == "012345678")
    assert sokha["orders_count"] == 2 and sokha["paid_orders"] == 2
    assert sokha["total_spent"] == "3.00"
