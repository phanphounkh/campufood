"""Order lifecycle: creation, access control, status transitions, cancellation, expiry."""

import logging
import uuid
from datetime import datetime, timedelta

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, bad_request, conflict, not_found
from app.core.security import hash_guest_token, new_guest_token, tokens_match
from app.models import Order, OrderItem, OrderStatus, Payment, PaymentStatus, User
from app.repositories.foods import lock_foods
from app.repositories.orders import get_order
from app.schemas.order import OrderCreate
from app.services.inventory import release_order_stock, reserve_stock
from app.services.payments.demo_khqr import get_provider
from app.services.store_settings import get_store_settings
from app.utils.money import line_total, to_money
from app.utils.time import local_tz, parse_hhmm, utcnow

logger = logging.getLogger("campuseats.orders")

MAX_PICKUP_DAYS_AHEAD = 7

# Allowed manual transitions. `pending_payment -> confirmed` is intentionally absent:
# only a verified payment can confirm an order.
TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING_PAYMENT: {OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.READY, OrderStatus.CANCELLED},
    OrderStatus.READY: {OrderStatus.COMPLETED, OrderStatus.CANCELLED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}


# ── Access control ─────────────────────────────────────────────


def can_access_order(order: Order, user: User | None, guest_token: str | None) -> bool:
    if user is not None and (user.is_staff or order.user_id == user.id):
        return True
    if guest_token and order.guest_access_token_hash:
        return tokens_match(hash_guest_token(guest_token), order.guest_access_token_hash)
    return False


async def get_accessible_order(
    session: AsyncSession,
    order_id: uuid.UUID,
    user: User | None,
    guest_token: str | None,
    *,
    for_update: bool = False,
) -> Order:
    order = await get_order(session, order_id, for_update=for_update)
    # Same 404 whether the order is missing or not yours: no existence oracle.
    if order is None or not can_access_order(order, user, guest_token):
        raise not_found("Order")
    return order


# ── Creation ───────────────────────────────────────────────────


async def _validate_pickup_time(session: AsyncSession, pickup: datetime) -> None:
    store = await get_store_settings(session)
    if not store.accepting_orders:
        raise conflict("STORE_CLOSED", "The canteen is not accepting online orders right now.")

    now = utcnow()
    earliest = now + timedelta(minutes=store.min_prep_minutes) - timedelta(minutes=2)
    if pickup < earliest:
        raise bad_request(
            "INVALID_PICKUP_TIME",
            f"Pickup time must be at least {store.min_prep_minutes} minutes from now.",
        )
    if pickup > now + timedelta(days=MAX_PICKUP_DAYS_AHEAD):
        raise bad_request(
            "INVALID_PICKUP_TIME", f"Pickup must be within {MAX_PICKUP_DAYS_AHEAD} days."
        )
    local = pickup.astimezone(local_tz()).time()
    if not parse_hhmm(store.opening_time) <= local <= parse_hhmm(store.closing_time):
        raise bad_request(
            "INVALID_PICKUP_TIME",
            f"Pickup time must be between {store.opening_time} and {store.closing_time}.",
        )


async def create_order(
    session: AsyncSession, data: OrderCreate, user: User | None
) -> tuple[Order, Payment, str]:
    """Create an order, reserve stock and open a pending payment — all in one transaction.

    Prices and availability come exclusively from the database (rows locked FOR UPDATE).
    """
    await _validate_pickup_time(session, data.pickup_time)
    store = await get_store_settings(session)

    requested = {item.food_id: item.quantity for item in data.items}
    foods = await lock_foods(session, list(requested))

    problems = []
    for food_id, qty in requested.items():
        food = foods.get(food_id)
        if food is None or food.is_archived:
            problems.append({"food_id": food_id, "reason": "not_found"})
        elif not food.is_available:
            problems.append({"food_id": food_id, "reason": "unavailable", "name": food.name_en})
        elif food.stock_quantity < qty:
            problems.append(
                {
                    "food_id": food_id,
                    "reason": "insufficient_stock",
                    "name": food.name_en,
                    "available": food.stock_quantity,
                }
            )
    if problems:
        raise conflict(
            "ITEMS_UNAVAILABLE", "Some items in your cart are no longer available.", problems
        )

    order_id = uuid.uuid4()
    items: list[OrderItem] = []
    subtotal = to_money(0)
    for food_id, qty in requested.items():
        food = foods[food_id]
        total = line_total(food.price, qty)
        subtotal += total
        items.append(
            OrderItem(
                food_id=food.id,
                food_name_snapshot=food.name_en,
                food_name_km_snapshot=food.name_km,
                quantity=qty,
                unit_price=food.price,
                line_total=total,
            )
        )
    total = to_money(subtotal)

    if data.expected_total is not None and to_money(data.expected_total) != total:
        raise conflict(
            "PRICE_CHANGED",
            "Prices changed since you added items to your cart. Please review your order.",
            {"expected_total": str(to_money(data.expected_total)), "actual_total": str(total)},
        )

    token = new_guest_token()
    order = Order(
        id=order_id,
        user_id=user.id if user else None,
        guest_access_token_hash=hash_guest_token(token),
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        student_id=data.student_id,
        pickup_time=data.pickup_time,
        notes=data.notes,
        subtotal=total,
        total=total,
        status=OrderStatus.PENDING_PAYMENT,
        items=items,
    )
    session.add(order)
    await session.flush()  # orders row must exist before inventory movements reference it

    for food_id, qty in requested.items():
        reserve_stock(session, foods[food_id], qty, order_id)

    provider = get_provider()
    payment = Payment(
        order_id=order.id,
        provider=provider.name,
        amount=total,
        currency="USD",
        status=PaymentStatus.PENDING,
        expires_at=utcnow() + timedelta(minutes=store.payment_expiry_minutes),
    )
    session.add(payment)
    await session.commit()
    await session.refresh(order, attribute_names=["payments", "items"])
    logger.info("Order %s created (%s USD)", order.order_number, total)
    return order, payment, token


# ── Cancellation, expiry and transitions ───────────────────────


async def _close_payments(session: AsyncSession, order: Order, *, expired: bool) -> None:
    provider = get_provider()
    for payment in order.payments:
        if payment.status == PaymentStatus.PENDING:
            payment.status = PaymentStatus.EXPIRED if expired else PaymentStatus.CANCELLED
        elif payment.status == PaymentStatus.PAID:
            provider.refund(payment)  # a real provider would request the refund here
            payment.status = PaymentStatus.REFUNDED
            payment.refunded_at = utcnow()


async def cancel_locked_order(
    session: AsyncSession, order: Order, reason: str, *, expired: bool = False
) -> None:
    """Cancel an order whose row is already locked. Releases stock once, refunds if paid."""
    if order.status in (OrderStatus.CANCELLED, OrderStatus.COMPLETED):
        raise conflict("INVALID_TRANSITION", f"A {order.status.value} order cannot be cancelled.")
    await _close_payments(session, order, expired=expired)
    await release_order_stock(session, order)
    order.status = OrderStatus.CANCELLED
    order.cancel_reason = reason.strip()[:300]


async def expire_if_due(session: AsyncSession, order: Order) -> bool:
    """Lazily expire an unpaid order whose payment window has passed. Commits if changed."""
    if order.status != OrderStatus.PENDING_PAYMENT:
        return False
    pending = [p for p in order.payments if p.status == PaymentStatus.PENDING]
    if pending and all(p.expires_at > utcnow() for p in pending):
        return False
    locked = await get_order(session, order.id, for_update=True)
    if locked is None or locked.status != OrderStatus.PENDING_PAYMENT:
        return False
    await cancel_locked_order(session, locked, "Payment window expired", expired=True)
    await session.commit()
    await session.refresh(locked, attribute_names=["payments"])
    logger.info("Order %s expired", locked.order_number)
    return True


async def expire_stale_orders(session: AsyncSession) -> int:
    """Background sweep: expire every unpaid order past its payment deadline."""
    order_ids = (
        await session.scalars(
            select(Payment.order_id)
            .join(Order, Order.id == Payment.order_id)
            .where(
                Payment.status == PaymentStatus.PENDING,
                Payment.expires_at <= utcnow(),
                Order.status == OrderStatus.PENDING_PAYMENT,
            )
            .limit(200)
        )
    ).all()
    expired = 0
    for order_id in set(order_ids):
        order = await get_order(session, order_id, for_update=True)
        if order is not None and order.status == OrderStatus.PENDING_PAYMENT:
            await cancel_locked_order(session, order, "Payment window expired", expired=True)
            expired += 1
        await session.commit()
    return expired


async def change_status(
    session: AsyncSession, order_id: uuid.UUID, target: OrderStatus, reason: str | None
) -> Order:
    order = await get_order(session, order_id, for_update=True)
    if order is None:
        raise not_found("Order")

    if order.status == target:
        return order  # idempotent: repeating the same action is harmless

    if target not in TRANSITIONS[order.status]:
        if target == OrderStatus.CONFIRMED:
            message = "Orders are confirmed automatically when payment succeeds."
        else:
            message = f"Cannot change an order from {order.status.value} to {target.value}."
        raise AppError(
            status.HTTP_409_CONFLICT,
            "INVALID_TRANSITION",
            message,
            {
                "from": order.status.value,
                "to": target.value,
                "allowed": sorted(s.value for s in TRANSITIONS[order.status]),
            },
        )

    if target == OrderStatus.CANCELLED:
        await cancel_locked_order(session, order, reason or "Cancelled by staff")
    else:
        order.status = target
    await session.commit()
    await session.refresh(order, attribute_names=["payments", "items", "updated_at"])
    logger.info("Order %s -> %s", order.order_number, target.value)
    return order


async def cancel_by_customer(
    session: AsyncSession, order_id: uuid.UUID, user: User | None, guest_token: str | None
) -> Order:
    order = await get_accessible_order(session, order_id, user, guest_token, for_update=True)
    if order.status != OrderStatus.PENDING_PAYMENT:
        raise conflict(
            "CANNOT_CANCEL",
            "This order is already paid. Please contact the canteen to cancel it.",
        )
    await cancel_locked_order(session, order, "Cancelled by customer")
    await session.commit()
    await session.refresh(order, attribute_names=["payments", "items", "updated_at"])
    return order
