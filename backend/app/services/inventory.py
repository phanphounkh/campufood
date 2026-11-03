"""Stock ledger operations.

All functions run inside the caller's transaction and expect the relevant `foods` rows to be
locked (SELECT ... FOR UPDATE) so concurrent orders cannot oversell.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import bad_request, not_found
from app.models import Food, InventoryMovement, InventoryReason, Order
from app.repositories.foods import get_food, lock_foods


def reserve_stock(session: AsyncSession, food: Food, quantity: int, order_id: uuid.UUID) -> None:
    if quantity <= 0 or food.stock_quantity < quantity:
        raise ValueError("insufficient stock")  # callers validate first; this is a safety net
    food.stock_quantity -= quantity
    session.add(
        InventoryMovement(
            food_id=food.id,
            order_id=order_id,
            quantity_change=-quantity,
            reason=InventoryReason.ORDER_RESERVED,
        )
    )


async def release_order_stock(session: AsyncSession, order: Order) -> bool:
    """Return an order's reserved stock exactly once.

    Returns False (and changes nothing) if the stock was already released. The partial
    unique index on (order_id, food_id, reason) enforces this at the database level too.
    """
    already = await session.scalar(
        select(InventoryMovement.id)
        .where(
            InventoryMovement.order_id == order.id,
            InventoryMovement.reason == InventoryReason.ORDER_RELEASED,
        )
        .limit(1)
    )
    if already is not None:
        return False

    reserved = (
        await session.execute(
            select(InventoryMovement.food_id, InventoryMovement.quantity_change).where(
                InventoryMovement.order_id == order.id,
                InventoryMovement.reason == InventoryReason.ORDER_RESERVED,
            )
        )
    ).all()
    if not reserved:
        return False

    foods = await lock_foods(session, [food_id for food_id, _ in reserved])
    for food_id, change in reserved:
        food = foods.get(food_id)
        if food is None:
            continue
        food.stock_quantity += -change
        session.add(
            InventoryMovement(
                food_id=food_id,
                order_id=order.id,
                quantity_change=-change,
                reason=InventoryReason.ORDER_RELEASED,
            )
        )
    return True


async def adjust_stock(
    session: AsyncSession,
    *,
    food_id: int,
    mode: str,
    quantity: int,
    reason: InventoryReason,
    note: str | None,
    user_id: int | None,
    is_available: bool | None = None,
) -> Food:
    food = await get_food(session, food_id, for_update=True)
    if food is None or food.is_archived:
        raise not_found("Food")

    change = quantity - food.stock_quantity if mode == "set" else quantity
    new_quantity = food.stock_quantity + change
    if new_quantity < 0:
        raise bad_request(
            "NEGATIVE_STOCK", f"Stock cannot go below zero (currently {food.stock_quantity})"
        )
    if change != 0:
        food.stock_quantity = new_quantity
        session.add(
            InventoryMovement(
                food_id=food.id,
                quantity_change=change,
                reason=reason,
                note=note,
                created_by_id=user_id,
            )
        )
    if is_available is not None:
        food.is_available = is_available
    await session.commit()
    await session.refresh(food)
    return food
