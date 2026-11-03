"""Role enforcement happens on the server, regardless of what the UI shows."""

import httpx
import pytest

from app.models import Food

FOOD = {"category_id": 1, "name_en": "New", "name_km": "ថ្មី", "price": "1.00"}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/admin/dashboard"),
        ("get", "/admin/reports"),
        ("get", "/admin/orders"),
        ("get", "/admin/inventory"),
        ("get", "/admin/customers"),
        ("get", "/admin/payments"),
        ("get", "/orders"),
    ],
)
async def test_admin_endpoints_require_login(
    client: httpx.AsyncClient, customer_client: httpx.AsyncClient, method: str, path: str
) -> None:
    assert (await getattr(client, method)(path)).status_code == 401
    assert (await getattr(customer_client, method)(path)).status_code == 403


async def test_menu_management_is_admin_only(
    menu: dict[str, Food],
    client: httpx.AsyncClient,
    customer_client: httpx.AsyncClient,
    staff_client: httpx.AsyncClient,
    admin_client: httpx.AsyncClient,
) -> None:
    assert (await client.post("/foods", json=FOOD)).status_code == 401
    assert (await customer_client.post("/foods", json=FOOD)).status_code == 403
    assert (await staff_client.post("/foods", json=FOOD)).status_code == 403
    food_id = menu["chicken_rice"].id
    assert (
        await staff_client.patch(f"/foods/{food_id}", json={"price": "0.10"})
    ).status_code == 403
    assert (await staff_client.delete(f"/foods/{food_id}")).status_code == 403
    assert (
        await staff_client.post("/categories", json={"name_en": "X", "name_km": "X"})
    ).status_code == 403
    assert (await admin_client.post("/foods", json=FOOD)).status_code == 201


async def test_staff_can_operate_but_not_configure(
    menu: dict[str, Food], staff_client: httpx.AsyncClient
) -> None:
    assert (await staff_client.get("/admin/dashboard")).status_code == 200
    assert (await staff_client.get("/admin/inventory")).status_code == 200
    restock = await staff_client.patch(
        f"/admin/inventory/{menu['fried_rice'].id}", json={"quantity": 5}
    )
    assert restock.status_code == 200
    assert (
        await staff_client.patch("/admin/settings", json={"store_name": "X"})
    ).status_code == 403
    assert (await staff_client.get("/admin/users")).status_code == 403


async def test_archived_foods_need_staff(
    menu: dict[str, Food], client: httpx.AsyncClient, admin_client: httpx.AsyncClient
) -> None:
    assert (await client.get("/foods", params={"include_archived": True})).status_code == 403
    assert (await admin_client.get("/foods", params={"include_archived": True})).status_code == 200


async def test_admin_cannot_lock_themselves_out(admin_client: httpx.AsyncClient) -> None:
    me = (await admin_client.get("/auth/me")).json()
    response = await admin_client.patch(f"/admin/users/{me['id']}", json={"role": "staff"})
    assert response.status_code == 409
