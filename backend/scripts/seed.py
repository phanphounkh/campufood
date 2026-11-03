"""Seed the database with categories, menu items, store settings and the first admin.

Usage (from backend/):
    uv run python scripts/seed.py                    # idempotent: safe to run repeatedly
    uv run python scripts/seed.py --demo-orders      # also generate ~30 days of sample orders
    uv run python scripts/seed.py --reset --demo-orders   # wipe data first (development only)

The admin password is taken from SEED_ADMIN_PASSWORD, or generated randomly and printed ONCE.
No well-known default password is ever created.
"""

import argparse
import asyncio
import os
import random
import secrets
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select, text

from app.core.config import BACKEND_DIR, settings
from app.core.database import SessionLocal, engine
from app.core.security import hash_guest_token, hash_password, new_guest_token
from app.models import (
    Category,
    Food,
    InventoryMovement,
    InventoryReason,
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentStatus,
    Setting,
    User,
    UserRole,
)
from app.schemas.admin import StoreSettings
from app.utils.money import line_total, to_money
from app.utils.time import local_now, local_tz

SEED_IMAGES = BACKEND_DIR / "seed_media" / "foods"

CATEGORIES = [
    ("rice", "Rice", "បាយ", 1),
    ("noodles", "Noodles", "មី និងគុយទាវ", 2),
    ("snacks", "Snacks", "អាហារសម្រន់", 3),
    ("drinks", "Drinks", "ភេសជ្ជៈ", 4),
    ("desserts", "Desserts", "បង្អែម", 5),
]


@dataclass
class SeedFood:
    slug: str
    category: str
    name_en: str
    name_km: str
    description_en: str
    description_km: str
    price: str
    stock: int
    featured: bool = False


FOODS = [
    SeedFood(
        "chicken-rice",
        "rice",
        "Chicken Rice",
        "បាយមាន់",
        "Tender poached chicken on fragrant rice cooked in chicken broth, with ginger-chili sauce.",
        "សាច់មាន់ស្ងោរទន់ៗ ជាមួយបាយក្រអូបចម្អិនក្នុងទឹកស៊ុបមាន់ និងទឹកជ្រលក់ខ្ញី និងម្ទេស។",
        "1.50",
        60,
        True,
    ),
    SeedFood(
        "fried-rice",
        "rice",
        "Fried Rice",
        "បាយឆា",
        "Wok-fried rice with egg, vegetables and tender chicken.",
        "បាយឆាលើខ្ទះក្តៅ ជាមួយពងមាន់ បន្លែ និងសាច់មាន់ទន់ៗ។",
        "1.75",
        50,
        True,
    ),
    SeedFood(
        "pork-rice",
        "rice",
        "Pork Rice",
        "បាយសាច់ជ្រូក",
        "Cambodian breakfast classic: coconut-marinated grilled pork over rice with pickles.",
        "អាហារពេលព្រឹកខ្មែរ៖ សាច់ជ្រូកអាំងប្រឡាក់ទឹកដូង លើបាយ ជាមួយជ្រក់។",
        "1.75",
        45,
        True,
    ),
    SeedFood(
        "fried-egg-rice",
        "rice",
        "Fried Egg Rice",
        "បាយពងមាន់ចៀន",
        "Jasmine rice topped with a crispy fried egg, cucumber and sweet soy sauce.",
        "បាយផ្កាម្លិះ ជាមួយពងមាន់ចៀនស្រួយ ត្រសក់ និងទឹកស៊ីអ៊ីវផ្អែម។",
        "1.50",
        40,
    ),
    SeedFood(
        "beef-lok-lak",
        "rice",
        "Beef Lok Lak",
        "ឡុកឡាក់សាច់គោ",
        "Stir-fried marinated beef cubes with fresh salad, rice and lime-pepper dip.",
        "សាច់គោឆាប្រឡាក់គ្រឿង ជាមួយសាឡាត់ស្រស់ បាយ និងទឹកម្រេចក្រូចឆ្មារ។",
        "2.50",
        25,
    ),
    SeedFood(
        "noodle-soup",
        "noodles",
        "Noodle Soup",
        "គុយទាវ",
        "Rice noodles in a clear pork broth with sliced pork, bean sprouts and fresh herbs.",
        "គុយទាវក្នុងទឹកស៊ុបឆ្អឹងជ្រូកថ្លា ជាមួយសាច់ជ្រូក សណ្តែកបណ្តុះ និងជីរស្រស់។",
        "1.50",
        50,
        True,
    ),
    SeedFood(
        "spicy-noodles",
        "noodles",
        "Spicy Noodles",
        "មីហឹរ",
        "Stir-fried egg noodles tossed in a fiery chili sauce with vegetables.",
        "មីឆាជាមួយទឹកម្ទេសហឹរ និងបន្លែ។",
        "1.75",
        35,
    ),
    SeedFood(
        "fried-noodles",
        "noodles",
        "Fried Noodles",
        "មីឆា",
        "Yellow noodles stir-fried with egg, greens and savoury soy sauce.",
        "មីលឿងឆាជាមួយពងមាន់ បន្លែបៃតង និងទឹកស៊ីអ៊ីវ។",
        "1.50",
        35,
    ),
    SeedFood(
        "num-banh-chok",
        "noodles",
        "Num Banh Chok",
        "នំបញ្ចុក",
        "Fresh rice noodles with Khmer fish curry and crunchy fresh vegetables.",
        "នំបញ្ចុកស្រស់ ជាមួយសម្លត្រីគ្រឿងខ្មែរ និងបន្លែស្រស់ៗ។",
        "1.25",
        30,
    ),
    SeedFood(
        "sandwich",
        "snacks",
        "Sandwich",
        "នំបុ័ងសាច់",
        "Crispy baguette with pâté, grilled pork, pickled papaya and chili.",
        "នំបុ័ងស្រួយ ជាមួយប៉ាតេ សាច់ជ្រូកអាំង ល្ហុងជ្រក់ និងម្ទេស។",
        "1.25",
        40,
    ),
    SeedFood(
        "spring-rolls",
        "snacks",
        "Fried Spring Rolls",
        "ចាយយ៉",
        "Golden spring rolls filled with pork and vegetables, with sweet dipping sauce.",
        "ចាយយ៉ចៀនពណ៌មាស ញាត់សាច់ជ្រូក និងបន្លែ ជាមួយទឹកជ្រលក់ផ្អែម។",
        "1.00",
        45,
    ),
    SeedFood(
        "beef-skewers",
        "snacks",
        "Beef Skewers",
        "សាច់គោចង្កាក់",
        "Lemongrass-marinated beef skewers grilled over charcoal.",
        "សាច់គោចង្កាក់ប្រឡាក់គ្រឿងស្លឹកគ្រៃ អាំងលើភ្លើងធ្យូង។",
        "1.50",
        30,
    ),
    SeedFood(
        "iced-milk-tea",
        "drinks",
        "Iced Milk Tea",
        "តែទឹកដោះគោទឹកកក",
        "Strong black tea with sweetened condensed milk, served over ice.",
        "តែខ្មៅខ្លាំង លាយទឹកដោះគោខាប់ផ្អែម ជាមួយទឹកកក។",
        "0.75",
        80,
        True,
    ),
    SeedFood(
        "iced-coffee",
        "drinks",
        "Iced Coffee",
        "កាហ្វេទឹកដោះគោទឹកកក",
        "Cambodian-style dark roast coffee with condensed milk over ice.",
        "កាហ្វេខ្មៅបែបខ្មែរ ជាមួយទឹកដោះគោខាប់ និងទឹកកក។",
        "0.75",
        80,
    ),
    SeedFood(
        "fresh-coconut",
        "drinks",
        "Fresh Coconut",
        "ដូងស្រស់",
        "Chilled young coconut, served whole with a straw.",
        "ដូងខ្ចីត្រជាក់ ផ្តល់ជូនទាំងផ្លែ ជាមួយបំពង់បឺត។",
        "1.00",
        30,
    ),
    SeedFood(
        "sugarcane-juice",
        "drinks",
        "Sugarcane Juice",
        "ទឹកអំពៅ",
        "Freshly pressed sugarcane juice with a hint of lime.",
        "ទឹកអំពៅច្របាច់ស្រស់ៗ លាយក្រូចឆ្មារបន្តិច។",
        "0.50",
        60,
    ),
    SeedFood(
        "mango-sticky-rice",
        "desserts",
        "Mango Sticky Rice",
        "បាយដំណើបស្វាយ",
        "Sweet coconut sticky rice with ripe mango slices.",
        "បាយដំណើបខ្ទិះដូងផ្អែម ជាមួយស្វាយទុំ។",
        "1.50",
        8,
        True,
    ),
    SeedFood(
        "pumpkin-custard",
        "desserts",
        "Pumpkin Custard",
        "សង់ខ្យាល្ពៅ",
        "Steamed coconut custard set inside a sweet pumpkin.",
        "សង់ខ្យាចំហុយក្នុងផ្លែល្ពៅផ្អែម។",
        "1.25",
        0,
    ),
    SeedFood(
        "banana-coconut-milk",
        "desserts",
        "Bananas in Coconut Milk",
        "ចេកខ្ទិះ",
        "Warm bananas simmered in coconut milk with tapioca pearls.",
        "ចេកស្ងោរខ្ទិះដូងក្តៅៗ ជាមួយគ្រាប់សាគូ។",
        "0.75",
        25,
    ),
]

DEFAULT_SETTINGS = StoreSettings(
    store_name="CampusEats",
    store_tagline="Student Canteen",
    store_phone="+855 12 345 678",
    store_email="hello@campuseats.local",
    store_address="Main Canteen, Building A, University Campus, Phnom Penh",
    opening_time="07:00",
    closing_time="17:00",
    facebook_url="https://www.facebook.com",
    telegram_url="https://telegram.org",
    instagram_url="https://www.instagram.com",
)

DEMO_CUSTOMERS = [
    ("Sokha Chan", "012345671"),
    ("Dara Kim", "015222333"),
    ("Srey Pov Heng", "098765432"),
    ("Vannak Lim", "077123456"),
    ("Bopha Seng", "089456123"),
    ("Pisey Touch", "016789012"),
    ("Rithy Sok", "010998877"),
    ("Chanthy Mao", "093112233"),
    ("Sophea Ouk", "011223344"),
    ("Kosal Nhem", "070555666"),
    ("Malis Pen", "081777888"),
    ("Visal Chea", "096333444"),
]


def log(msg: str) -> None:
    print(f"  {msg}")


async def reset(session) -> None:
    await session.execute(
        text(
            "TRUNCATE inventory_movements, payments, order_items, orders, foods, categories, "
            "settings RESTART IDENTITY CASCADE"
        )
    )
    await session.execute(text("ALTER SEQUENCE order_number_seq RESTART WITH 1001"))
    await session.commit()
    log("Existing menu, order and settings data removed (users kept).")


def copy_image(slug: str) -> str | None:
    source = SEED_IMAGES / f"{slug}.jpg"
    if not source.exists():
        return None
    target_dir = settings.media_root / "foods"
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target_dir / f"{slug}.jpg")
    return f"{settings.media_url_prefix}/foods/{slug}.jpg"


async def seed_catalog(session) -> dict[str, Food]:
    categories: dict[str, Category] = {}
    for slug, name_en, name_km, order in CATEGORIES:
        category = await session.scalar(select(Category).where(Category.slug == slug))
        if category is None:
            category = Category(slug=slug, name_en=name_en, name_km=name_km, sort_order=order)
            session.add(category)
        categories[slug] = category
    await session.flush()

    foods: dict[str, Food] = {}
    created = 0
    for item in FOODS:
        image_url = copy_image(item.slug)
        food = (
            (await session.scalars(select(Food).where(Food.name_en == item.name_en)))
            .unique()
            .one_or_none()
        )
        if food is None:
            food = Food(
                category_id=categories[item.category].id,
                name_en=item.name_en,
                name_km=item.name_km,
                description_en=item.description_en,
                description_km=item.description_km,
                price=Decimal(item.price),
                image_url=image_url,
                stock_quantity=item.stock,
                is_available=True,
                is_featured=item.featured,
            )
            session.add(food)
            await session.flush()
            if item.stock:
                session.add(
                    InventoryMovement(
                        food_id=food.id,
                        quantity_change=item.stock,
                        reason=InventoryReason.INITIAL,
                        note="Seed data",
                    )
                )
            created += 1
        elif image_url and not food.image_url:
            food.image_url = image_url
        foods[item.slug] = food
    await session.commit()
    log(f"Categories: {len(categories)} • Foods: {len(foods)} ({created} new)")
    missing = [f.slug for f in FOODS if not (SEED_IMAGES / f"{f.slug}.jpg").exists()]
    if missing:
        log(f"Note: no seed image for {', '.join(missing)} (a placeholder will be shown)")
    return foods


async def seed_settings(session) -> None:
    existing = set((await session.scalars(select(Setting.key))).all())
    added = 0
    for key, value in DEFAULT_SETTINGS.model_dump().items():
        if key not in existing:
            session.add(Setting(key=key, value=value))
            added += 1
    await session.commit()
    log(f"Settings: {added} default value(s) added")


async def seed_admin(session) -> None:
    email = (os.environ.get("SEED_ADMIN_EMAIL") or "admin@campuseats.local").strip().lower()
    password = os.environ.get("SEED_ADMIN_PASSWORD") or ""
    existing = await session.scalar(select(User).where(func.lower(User.email) == email))
    if existing:
        log(f"Admin account {email} already exists (password unchanged).")
        return
    generated = not password
    if generated:
        password = secrets.token_urlsafe(12)
    elif len(password) < 10:
        raise SystemExit("SEED_ADMIN_PASSWORD must be at least 10 characters.")
    session.add(
        User(
            name="Canteen Admin",
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
        )
    )
    await session.commit()
    print()
    print("  ┌──────────────────────────────────────────────────────────┐")
    print("  │ Admin account created                                    │")
    print(f"  │   Email:    {email:<45}│")
    if generated:
        print(f"  │   Password: {password:<45}│")
        print("  │ Store it now — it is not saved anywhere and won't be     │")
        print("  │ shown again. (Set SEED_ADMIN_PASSWORD to choose one.)    │")
    else:
        print("  │   Password: (from SEED_ADMIN_PASSWORD)                   │")
    print("  └──────────────────────────────────────────────────────────┘")
    print()


async def seed_demo_orders(session, foods: dict[str, Food], days: int) -> None:
    """Generate realistic, internally consistent order history for the dashboard."""
    already = await session.scalar(select(func.count(Order.id)))
    if already:
        log(f"Demo orders skipped: {already} order(s) already exist.")
        return

    rng = random.Random(2026)
    tz = local_tz()
    today = local_now().date()
    menu = [f for f in foods.values() if f.stock_quantity > 0 or f.name_en != "Pumpkin Custard"]
    weights = [6 if f.is_featured else 2 for f in menu]
    count = 0

    for day_offset in range(days, -1, -1):
        day = today - timedelta(days=day_offset)
        weekday_factor = 0.45 if day.weekday() >= 5 else 1.0
        n_orders = int(rng.randint(9, 18) * weekday_factor) + (4 if day_offset < 7 else 0)
        for _ in range(n_orders):
            hour = rng.choices(
                [7, 8, 9, 10, 11, 12, 13, 14, 15, 16], [4, 6, 3, 3, 9, 10, 6, 3, 3, 2]
            )[0]
            created = datetime(
                day.year,
                day.month,
                day.day,
                hour,
                rng.randint(0, 59),
                rng.randint(0, 59),
                tzinfo=tz,
            )
            if created > local_now() - timedelta(minutes=5):
                continue
            name, phone = rng.choice(DEMO_CUSTOMERS)
            picks = rng.choices(menu, weights, k=rng.randint(1, 3))
            items: dict[int, tuple[Food, int]] = {}
            for food in picks:
                qty = items.get(food.id, (food, 0))[1] + rng.choice([1, 1, 1, 2])
                items[food.id] = (food, qty)

            order_items = [
                OrderItem(
                    food_id=f.id,
                    food_name_snapshot=f.name_en,
                    food_name_km_snapshot=f.name_km,
                    quantity=q,
                    unit_price=f.price,
                    line_total=line_total(f.price, q),
                )
                for f, q in items.values()
            ]
            total = to_money(sum((i.line_total for i in order_items), Decimal(0)))

            is_today = day_offset == 0
            roll = rng.random()
            if is_today and created > local_now() - timedelta(hours=1):
                status = rng.choice(
                    [OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY]
                )
            elif roll < 0.06:
                status = OrderStatus.CANCELLED
            else:
                status = OrderStatus.COMPLETED
            refunded = status == OrderStatus.CANCELLED and rng.random() < 0.5

            order = Order(
                customer_name=name,
                customer_phone=phone,
                guest_access_token_hash=hash_guest_token(new_guest_token()),
                pickup_time=created + timedelta(minutes=rng.choice([15, 20, 30, 45])),
                subtotal=total,
                total=total,
                status=status,
                cancel_reason=(
                    "Customer requested cancellation"
                    if refunded
                    else "Payment window expired"
                    if status == OrderStatus.CANCELLED
                    else None
                ),
                items=order_items,
                created_at=created,
                updated_at=created + timedelta(minutes=25),
            )
            session.add(order)
            await session.flush()

            paid_at = created + timedelta(seconds=rng.randint(20, 150))
            if status == OrderStatus.CANCELLED and not refunded:
                pay_status, paid, refunded_at = PaymentStatus.EXPIRED, None, None
            elif refunded:
                pay_status, paid = PaymentStatus.REFUNDED, paid_at
                refunded_at = paid_at + timedelta(minutes=10)
            else:
                pay_status, paid, refunded_at = PaymentStatus.PAID, paid_at, None
            session.add(
                Payment(
                    order_id=order.id,
                    provider="demo_khqr",
                    amount=total,
                    currency="USD",
                    status=pay_status,
                    transaction_reference=(
                        f"DEMO-{secrets.token_hex(6).upper()}" if paid else None
                    ),
                    expires_at=created + timedelta(minutes=15),
                    paid_at=paid,
                    refunded_at=refunded_at,
                    created_at=created,
                    updated_at=refunded_at or paid or created,
                )
            )
            count += 1
    await session.commit()
    log(f"Demo orders: {count} generated across {days + 1} days (historic, no stock impact)")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed CampusEats data")
    parser.add_argument("--reset", action="store_true", help="Delete menu/order data first")
    parser.add_argument("--demo-orders", action="store_true", help="Generate sample order history")
    parser.add_argument("--days", type=int, default=30, help="Days of demo history (default 30)")
    args = parser.parse_args()

    if args.reset and settings.app_env == "production":
        raise SystemExit("Refusing to --reset in production.")

    print("Seeding CampusEats database…")
    async with SessionLocal() as session:
        if args.reset:
            await reset(session)
        await seed_settings(session)
        foods = await seed_catalog(session)
        await seed_admin(session)
        if args.demo_orders:
            await seed_demo_orders(session, foods, args.days)
    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
