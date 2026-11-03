import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderStatus
from app.utils.text import escape_like, normalize_phone


async def get_order(
    session: AsyncSession, order_id: uuid.UUID, *, for_update: bool = False
) -> Order | None:
    stmt = select(Order).where(Order.id == order_id)
    if for_update:
        # populate_existing refreshes an already-loaded instance with the locked row.
        stmt = stmt.with_for_update(of=Order).execution_options(populate_existing=True)
    return (await session.scalars(stmt)).one_or_none()


async def list_orders(
    session: AsyncSession,
    *,
    statuses: list[OrderStatus] | None = None,
    search: str | None = None,
    user_id: int | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Order], int]:
    stmt = select(Order)
    if statuses:
        stmt = stmt.where(Order.status.in_(statuses))
    if user_id is not None:
        stmt = stmt.where(Order.user_id == user_id)
    if created_from is not None:
        stmt = stmt.where(Order.created_at >= created_from)
    if created_to is not None:
        stmt = stmt.where(Order.created_at < created_to)
    if search:
        term = search.strip()
        pattern = f"%{escape_like(term)}%"
        conditions = [
            Order.order_number.ilike(pattern, escape="\\"),
            Order.customer_name.ilike(pattern, escape="\\"),
        ]
        if term.isdigit():
            conditions.append(Order.order_number == f"CE-{term}")
        phone = normalize_phone(term)
        if len(phone) >= 3:
            conditions.append(Order.customer_phone.contains(phone))
        stmt = stmt.where(or_(*conditions))

    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = await session.scalars(
        stmt.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return list(rows.all()), int(total or 0)


async def count_by_status(session: AsyncSession) -> dict[str, int]:
    rows = await session.execute(select(Order.status, func.count()).group_by(Order.status))
    return {status.value: count for status, count in rows.all()}
