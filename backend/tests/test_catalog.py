import httpx

from app.models import Food


async def test_public_menu_listing_and_filters(
    menu: dict[str, Food], client: httpx.AsyncClient
) -> None:
    response = await client.get("/foods")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    chicken = next(f for f in body["items"] if f["name_en"] == "Chicken Rice")
    assert chicken["price"] == "1.50"  # money is a fixed 2-decimal string
    assert chicken["name_km"] == "បាយមាន់"
    assert chicken["category"]["slug"] == "rice"
    sold_out = next(f for f in body["items"] if f["name_en"] == "Pork Rice")
    assert sold_out["is_sold_out"] is True

    drinks = (await client.get("/foods", params={"category": "drinks"})).json()
    assert {f["name_en"] for f in drinks["items"]} == {"Iced Milk Tea", "Iced Coffee"}

    found = (await client.get("/foods", params={"search": "fried"})).json()
    assert [f["name_en"] for f in found["items"]] == ["Fried Rice"]

    khmer = (await client.get("/foods", params={"search": "បាយមាន់"})).json()
    assert [f["name_en"] for f in khmer["items"]] == ["Chicken Rice"]

    cheap_first = (await client.get("/foods", params={"sort": "price_asc"})).json()["items"]
    prices = [f["price"] for f in cheap_first]
    assert prices == sorted(prices, key=lambda p: float(p))

    available = (await client.get("/foods", params={"available_only": True})).json()
    assert {f["name_en"] for f in available["items"]} == {
        "Chicken Rice",
        "Fried Rice",
        "Iced Milk Tea",
    }


async def test_food_crud(
    menu: dict[str, Food], admin_client: httpx.AsyncClient, client: httpx.AsyncClient
) -> None:
    category_id = menu["chicken_rice"].category_id
    created = await admin_client.post(
        "/foods",
        json={
            "category_id": category_id,
            "name_en": "  Beef   Lok Lak ",
            "name_km": "ឡុកឡាក់",
            "description_en": "Stir-fried beef",
            "price": "2.50",
            "stock_quantity": 12,
            "is_featured": True,
            "image_url": "/media/foods/abc123.webp",
        },
    )
    assert created.status_code == 201, created.text
    food = created.json()
    assert food["name_en"] == "Beef Lok Lak"
    assert food["price"] == "2.50"

    updated = await admin_client.patch(
        f"/foods/{food['id']}", json={"price": "2.75", "description_km": "សាច់គោ"}
    )
    assert updated.status_code == 200
    assert updated.json()["price"] == "2.75"
    assert updated.json()["description_km"] == "សាច់គោ"
    assert updated.json()["name_en"] == "Beef Lok Lak"  # untouched fields are kept

    archived = await admin_client.delete(f"/foods/{food['id']}")
    assert archived.status_code == 200 and archived.json()["is_archived"] is True
    public_names = [f["name_en"] for f in (await client.get("/foods")).json()["items"]]
    assert "Beef Lok Lak" not in public_names
    assert (await client.get(f"/foods/{food['id']}")).status_code == 404

    restored = await admin_client.patch(f"/foods/{food['id']}", json={"is_archived": False})
    assert restored.json()["is_archived"] is False


async def test_food_validation(menu: dict[str, Food], admin_client: httpx.AsyncClient) -> None:
    base = {"category_id": menu["chicken_rice"].category_id, "name_en": "X", "name_km": "X"}
    for bad in [
        {**base, "price": "-1"},
        {**base, "price": "0"},
        {**base, "price": "1.505"},
        {**base, "price": "1.00", "image_url": "javascript:alert(1)"},
        {**base, "price": "1.00", "image_url": "/media/../../etc/passwd.png"},
        {**base, "price": "1.00", "name_en": "   "},
        {**base, "price": "1.00", "stock_quantity": -3},
    ]:
        response = await admin_client.post("/foods", json=bad)
        assert response.status_code == 422, bad
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    missing_category = await admin_client.post(
        "/foods", json={**base, "category_id": 999, "price": "1"}
    )
    assert missing_category.status_code == 400


async def test_category_crud(
    menu: dict[str, Food], admin_client: httpx.AsyncClient, client: httpx.AsyncClient
) -> None:
    created = await admin_client.post(
        "/categories", json={"name_en": "Snacks & Bites", "name_km": "អាហារសម្រន់"}
    )
    assert created.status_code == 201
    category = created.json()
    assert category["slug"] == "snacks-bites"

    duplicate = await admin_client.post(
        "/categories", json={"name_en": "Other", "name_km": "X", "slug": "snacks-bites"}
    )
    assert duplicate.status_code == 409

    renamed = await admin_client.patch(f"/categories/{category['id']}", json={"name_en": "Snacks"})
    assert renamed.json()["name_en"] == "Snacks"

    listing = (await client.get("/categories")).json()
    rice = next(c for c in listing if c["slug"] == "rice")
    assert rice["food_count"] == 3

    in_use = await admin_client.delete(f"/categories/{rice['id']}")
    assert in_use.status_code == 409 and in_use.json()["error"]["code"] == "CATEGORY_IN_USE"
    assert (await admin_client.delete(f"/categories/{category['id']}")).status_code == 204
