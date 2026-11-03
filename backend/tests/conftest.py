"""Test fixtures.

Tests run against a real PostgreSQL database (`campuseats_test`, created by the Docker init
script) because row locking, partial unique indexes and NUMERIC behaviour matter here.
The schema is built with the real Alembic migrations, then truncated between tests.
"""

import os
import tempfile
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from dotenv import dotenv_values

# ── Configure the environment BEFORE importing the application ──
_env = {**dotenv_values(Path(__file__).resolve().parents[2] / ".env"), **os.environ}
_test_url = _env.get("TEST_DATABASE_URL") or (
    (_env.get("DATABASE_URL") or "").rstrip("/") + "_test"
)
if not _test_url or not _test_url.endswith("_test"):
    raise RuntimeError("TEST_DATABASE_URL must point to a database whose name ends in _test")
os.environ.update(
    {
        "APP_ENV": "test",
        "DATABASE_URL": _test_url,
        "RUN_BACKGROUND_JOBS": "false",
        "DEMO_PAYMENTS_ENABLED": "true",
        "COOKIE_SECURE": "false",
        "TRUST_PROXY_HEADERS": "false",
        "JWT_SECRET": "test-secret-" + "x" * 40,
        "MEDIA_ROOT": tempfile.mkdtemp(prefix="campuseats-media-"),
    }
)

import httpx  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from alembic import command  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Category, Food, InventoryMovement, InventoryReason, User, UserRole  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]
PASSWORD = "correct-horse-battery"
TZ = ZoneInfo("Asia/Phnom_Penh")


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    """Recreate the test schema from scratch using the Alembic migrations."""
    import asyncio

    async def _reset_schema() -> None:
        engine = create_async_engine(_test_url)
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
        await engine.dispose()

    asyncio.run(_reset_schema())
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.attributes["database_url"] = _test_url
    command.upgrade(cfg, "head")


TABLES = "inventory_movements, payments, order_items, orders, foods, categories, settings, users"


@pytest.fixture(autouse=True)
async def clean_db() -> AsyncIterator[None]:
    async with SessionLocal() as session:
        await session.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
        await session.execute(text("ALTER SEQUENCE order_number_seq RESTART WITH 1001"))
        await session.commit()
    limiter.reset()
    yield


@pytest.fixture
async def menu() -> dict[str, Food]:
    """A small menu: two categories, regular, low-stock, sold-out and unavailable items."""
    async with SessionLocal() as session:
        rice = Category(slug="rice", name_en="Rice", name_km="បាយ", sort_order=1)
        drinks = Category(slug="drinks", name_en="Drinks", name_km="ភេសជ្ជៈ", sort_order=2)
        session.add_all([rice, drinks])
        await session.flush()
        foods = {
            "chicken_rice": Food(
                category_id=rice.id,
                name_en="Chicken Rice",
                name_km="បាយមាន់",
                price=Decimal("1.50"),
                stock_quantity=10,
                is_featured=True,
            ),
            "fried_rice": Food(
                category_id=rice.id,
                name_en="Fried Rice",
                name_km="បាយឆា",
                price=Decimal("1.75"),
                stock_quantity=3,
            ),
            "milk_tea": Food(
                category_id=drinks.id,
                name_en="Iced Milk Tea",
                name_km="តែទឹកដោះគោទឹកកក",
                price=Decimal("0.75"),
                stock_quantity=50,
            ),
            "sold_out": Food(
                category_id=rice.id,
                name_en="Pork Rice",
                name_km="បាយសាច់ជ្រូក",
                price=Decimal("1.75"),
                stock_quantity=0,
            ),
            "unavailable": Food(
                category_id=drinks.id,
                name_en="Iced Coffee",
                name_km="កាហ្វេ",
                price=Decimal("0.75"),
                stock_quantity=20,
                is_available=False,
            ),
        }
        session.add_all(foods.values())
        await session.flush()
        for food in foods.values():
            if food.stock_quantity:
                session.add(
                    InventoryMovement(
                        food_id=food.id,
                        quantity_change=food.stock_quantity,
                        reason=InventoryReason.INITIAL,
                    )
                )
        await session.commit()
        return foods


async def _make_user(role: UserRole, email: str) -> User:
    async with SessionLocal() as session:
        user = User(
            name=f"{role.value.title()} User",
            email=email,
            role=role,
            password_hash=hash_password(PASSWORD),
        )
        session.add(user)
        await session.commit()
        return user


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver.local/api/v1"
    )


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    async with _client() as c:
        yield c


async def login(c: httpx.AsyncClient, email: str, password: str = PASSWORD) -> httpx.Response:
    response = await c.post("/auth/login", json={"email": email, "password": password})
    if response.status_code == 200:
        # Browsers echo the readable CSRF cookie in a header (double-submit pattern).
        c.headers["X-CSRF-Token"] = c.cookies["ce_csrf"]
    return response


@pytest.fixture
async def admin_client() -> AsyncIterator[httpx.AsyncClient]:
    await _make_user(UserRole.ADMIN, "admin@test.example")
    async with _client() as c:
        assert (await login(c, "admin@test.example")).status_code == 200
        yield c


@pytest.fixture
async def staff_client() -> AsyncIterator[httpx.AsyncClient]:
    await _make_user(UserRole.STAFF, "staff@test.example")
    async with _client() as c:
        assert (await login(c, "staff@test.example")).status_code == 200
        yield c


@pytest.fixture
async def customer_client() -> AsyncIterator[httpx.AsyncClient]:
    await _make_user(UserRole.CUSTOMER, "student@test.example")
    async with _client() as c:
        assert (await login(c, "student@test.example")).status_code == 200
        yield c


def pickup_time(days: int = 1, hour: int = 12) -> str:
    """A valid pickup time: tomorrow at noon, canteen time."""
    base = datetime.now(TZ) + timedelta(days=days)
    return base.replace(hour=hour, minute=0, second=0, microsecond=0).isoformat()


async def place_order(
    c: httpx.AsyncClient, items: list[tuple[Food, int]], **overrides: Any
) -> httpx.Response:
    body = {
        "customer_name": "Sokha Chan",
        "customer_phone": "012 345 678",
        "pickup_time": pickup_time(),
        "items": [{"food_id": food.id, "quantity": qty} for food, qty in items],
        **overrides,
    }
    return await c.post("/orders", json=body)


async def stock_of(food: Food) -> int:
    async with SessionLocal() as session:
        return (
            await session.execute(
                text("SELECT stock_quantity FROM foods WHERE id = :id"), {"id": food.id}
            )
        ).scalar_one()
