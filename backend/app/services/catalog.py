"""Category and food management."""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import bad_request, conflict, not_found
from app.models import Category, Food, InventoryMovement, InventoryReason
from app.repositories.foods import get_food
from app.schemas.catalog import (
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    FoodCreate,
    FoodUpdate,
)
from app.utils.text import slugify

# ── Categories ─────────────────────────────────────────────────


async def list_categories(
    session: AsyncSession, *, include_empty: bool = True
) -> list[CategoryOut]:
    counts = (
        select(Food.category_id, func.count(Food.id).label("n"))
        .where(Food.is_archived.is_(False))
        .group_by(Food.category_id)
        .subquery()
    )
    rows = await session.execute(
        select(Category, func.coalesce(counts.c.n, 0))
        .outerjoin(counts, counts.c.category_id == Category.id)
        .order_by(Category.sort_order, Category.name_en)
    )
    result = []
    for category, count in rows.all():
        if include_empty or count:
            out = CategoryOut.model_validate(category)
            out.food_count = count
            result.append(out)
    return result


async def _commit_unique(session: AsyncSession, what: str) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise conflict("DUPLICATE", f"A {what} with this slug already exists.") from exc


async def create_category(session: AsyncSession, data: CategoryCreate) -> Category:
    slug = data.slug or slugify(data.name_en)
    if not slug:
        raise bad_request("INVALID_SLUG", "Could not derive a slug; please provide one.")
    category = Category(
        name_en=data.name_en, name_km=data.name_km, slug=slug, sort_order=data.sort_order
    )
    session.add(category)
    await _commit_unique(session, "category")
    await session.refresh(category)
    return category


async def update_category(
    session: AsyncSession, category_id: int, data: CategoryUpdate
) -> Category:
    category = await session.get(Category, category_id)
    if category is None:
        raise not_found("Category")
    for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(category, field, value)
    await _commit_unique(session, "category")
    await session.refresh(category)
    return category


async def delete_category(session: AsyncSession, category_id: int) -> None:
    category = await session.get(Category, category_id)
    if category is None:
        raise not_found("Category")
    in_use = await session.scalar(
        select(func.count(Food.id)).where(Food.category_id == category_id)
    )
    if in_use:
        raise conflict(
            "CATEGORY_IN_USE",
            f"This category still has {in_use} food item(s). Move or delete them first.",
        )
    await session.delete(category)
    await session.commit()


# ── Foods ──────────────────────────────────────────────────────


async def _require_category(session: AsyncSession, category_id: int) -> None:
    if await session.get(Category, category_id) is None:
        raise bad_request("INVALID_CATEGORY", "Category does not exist.")


async def create_food(session: AsyncSession, data: FoodCreate, user_id: int | None) -> Food:
    await _require_category(session, data.category_id)
    food = Food(**data.model_dump())
    session.add(food)
    await session.flush()
    if food.stock_quantity:
        session.add(
            InventoryMovement(
                food_id=food.id,
                quantity_change=food.stock_quantity,
                reason=InventoryReason.INITIAL,
                created_by_id=user_id,
            )
        )
    await session.commit()
    return await _reload(session, food.id)


async def update_food(
    session: AsyncSession, food_id: int, data: FoodUpdate, user_id: int | None
) -> Food:
    food = await get_food(session, food_id, for_update=True)
    if food is None:
        raise not_found("Food")
    changes = data.model_dump(exclude_unset=True)
    # Required columns cannot be nulled; image_url may be cleared explicitly.
    changes = {k: v for k, v in changes.items() if v is not None or k == "image_url"}
    if "category_id" in changes:
        await _require_category(session, changes["category_id"])
    if "stock_quantity" in changes:
        delta = changes["stock_quantity"] - food.stock_quantity
        if delta:
            session.add(
                InventoryMovement(
                    food_id=food.id,
                    quantity_change=delta,
                    reason=InventoryReason.MANUAL_ADJUSTMENT,
                    note="Edited from menu form",
                    created_by_id=user_id,
                )
            )
    for field, value in changes.items():
        setattr(food, field, value)
    await session.commit()
    return await _reload(session, food.id)


async def archive_food(session: AsyncSession, food_id: int) -> Food:
    """Soft delete: archived foods vanish from the menu but keep order history intact."""
    food = await get_food(session, food_id, for_update=True)
    if food is None:
        raise not_found("Food")
    food.is_archived = True
    food.is_featured = False
    await session.commit()
    return await _reload(session, food.id)


async def _reload(session: AsyncSession, food_id: int) -> Food:
    food = (
        (
            await session.scalars(
                select(Food).where(Food.id == food_id).execution_options(populate_existing=True)
            )
        )
        .unique()
        .one()
    )
    return food
