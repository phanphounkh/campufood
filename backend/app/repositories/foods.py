from typing import Literal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Food
from app.utils.text import escape_like

FoodSort = Literal["featured", "price_asc", "price_desc", "name", "newest"]


def _filtered(
    *,
    category: str | None,
    search: str | None,
    available_only: bool,
    featured: bool | None,
    include_archived: bool,
) -> Select[tuple[Food]]:
    stmt = select(Food).join(Food.category)
    if not include_archived:
        stmt = stmt.where(Food.is_archived.is_(False))
    if category and category != "all":
        stmt = stmt.where(Category.slug == category)
    if search:
        pattern = f"%{escape_like(search.strip())}%"
        stmt = stmt.where(
            or_(
                Food.name_en.ilike(pattern, escape="\\"),
                Food.name_km.ilike(pattern, escape="\\"),
                Food.description_en.ilike(pattern, escape="\\"),
            )
        )
    if available_only:
        stmt = stmt.where(Food.is_available.is_(True), Food.stock_quantity > 0)
    if featured is not None:
        stmt = stmt.where(Food.is_featured.is_(featured))
    return stmt


_ORDERING = {
    "featured": (Food.is_featured.desc(), Category.sort_order, Food.name_en),
    "price_asc": (Food.price.asc(), Food.name_en),
    "price_desc": (Food.price.desc(), Food.name_en),
    "name": (Food.name_en,),
    "newest": (Food.created_at.desc(), Food.id.desc()),
}


async def list_foods(
    session: AsyncSession,
    *,
    category: str | None = None,
    search: str | None = None,
    available_only: bool = False,
    featured: bool | None = None,
    include_archived: bool = False,
    sort: FoodSort = "featured",
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Food], int]:
    base = _filtered(
        category=category,
        search=search,
        available_only=available_only,
        featured=featured,
        include_archived=include_archived,
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    rows = await session.scalars(
        base.order_by(*_ORDERING[sort]).offset((page - 1) * page_size).limit(page_size)
    )
    return list(rows.unique()), int(total or 0)


async def get_food(session: AsyncSession, food_id: int, *, for_update: bool = False) -> Food | None:
    stmt = select(Food).where(Food.id == food_id)
    if for_update:
        stmt = stmt.with_for_update(of=Food)
    return (await session.scalars(stmt)).unique().one_or_none()


async def lock_foods(session: AsyncSession, food_ids: list[int]) -> dict[int, Food]:
    """Row-lock foods in a consistent (id) order so concurrent orders cannot deadlock."""
    stmt = select(Food).where(Food.id.in_(food_ids)).order_by(Food.id).with_for_update(of=Food)
    foods = (await session.scalars(stmt)).unique().all()
    return {food.id: food for food in foods}
