import httpx

from app.core.rate_limit import limiter
from app.models import UserRole
from tests.conftest import PASSWORD, _make_user, login


async def test_login_sets_http_only_session_cookie(client: httpx.AsyncClient) -> None:
    await _make_user(UserRole.ADMIN, "boss@test.example")
    response = await client.post(
        "/auth/login", json={"email": "Boss@Test.example", "password": PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["role"] == "admin"
    assert "password_hash" not in body["user"]
    cookies = response.headers.get_list("set-cookie")
    session_cookie = next(c for c in cookies if c.startswith("ce_session="))
    csrf_cookie = next(c for c in cookies if c.startswith("ce_csrf="))
    assert "HttpOnly" in session_cookie and "SameSite=lax" in session_cookie
    assert "HttpOnly" not in csrf_cookie  # the web app must be able to read it


async def test_wrong_password_and_unknown_email_look_identical(client: httpx.AsyncClient) -> None:
    await _make_user(UserRole.ADMIN, "boss@test.example")
    wrong = await client.post("/auth/login", json={"email": "boss@test.example", "password": "x"})
    unknown = await client.post(
        "/auth/login", json={"email": "nobody@test.example", "password": "x"}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


async def test_me_and_logout(client: httpx.AsyncClient) -> None:
    assert (await client.get("/auth/me")).status_code == 401
    await _make_user(UserRole.STAFF, "staff@test.example")
    await login(client, "staff@test.example")
    me = await client.get("/auth/me")
    assert me.status_code == 200 and me.json()["role"] == "staff"
    assert (await client.post("/auth/logout")).status_code == 200
    assert (await client.get("/auth/me")).status_code == 401


async def test_customer_cannot_use_admin_login(client: httpx.AsyncClient) -> None:
    await _make_user(UserRole.CUSTOMER, "student@test.example")
    response = await client.post(
        "/auth/login",
        json={"email": "student@test.example", "password": PASSWORD, "require_staff": True},
    )
    assert response.status_code == 403
    assert "ce_session" not in response.cookies


async def test_register_customer(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={"name": "Dara Kim", "email": "dara@test.example", "password": "longenough1"},
    )
    assert response.status_code == 201
    assert response.json()["user"]["role"] == "customer"
    duplicate = await client.post(
        "/auth/register",
        json={"name": "Dara Kim", "email": "DARA@test.example", "password": "longenough1"},
    )
    assert duplicate.status_code == 409


async def test_csrf_token_required_for_cookie_authenticated_writes(
    admin_client: httpx.AsyncClient,
) -> None:
    payload = {"name_en": "Soup", "name_km": "ស៊ុប"}
    token = admin_client.headers.pop("X-CSRF-Token")
    missing = await admin_client.post("/categories", json=payload)
    assert missing.status_code == 403 and missing.json()["error"]["code"] == "CSRF_FAILED"
    wrong = await admin_client.post(
        "/categories", json=payload, headers={"X-CSRF-Token": "not-the-token"}
    )
    assert wrong.status_code == 403
    ok = await admin_client.post("/categories", json=payload, headers={"X-CSRF-Token": token})
    assert ok.status_code == 201


async def test_cross_origin_writes_are_blocked(admin_client: httpx.AsyncClient) -> None:
    response = await admin_client.post(
        "/categories",
        json={"name_en": "Soup", "name_km": "ស៊ុប"},
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403


async def test_login_is_rate_limited(client: httpx.AsyncClient) -> None:
    limiter.reset()
    codes = [
        (
            await client.post("/auth/login", json={"email": "a@b.example", "password": "x"})
        ).status_code
        for _ in range(11)
    ]
    assert codes[:10] == [401] * 10
    assert codes[10] == 429
