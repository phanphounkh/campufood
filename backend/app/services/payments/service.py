"""Provider-independent payment workflow: checkout data, confirmation, status.

`confirm_payment` is the only code path that can move an order to `confirmed`. It locks the
order and payment rows, so concurrent or repeated confirmations are serialized, and it is
idempotent: confirming an already-paid payment returns the same result without side effects.
"""

import logging
import uuid
from datetime import timedelta

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError, conflict, not_found
from app.models import Order, OrderStatus, Payment, PaymentStatus, User
from app.schemas.order import PaymentCheckoutOut
from app.schemas.payment import DemoConfirmOut, PaymentStatusOut
from app.services.orders import cancel_locked_order, expire_if_due, get_accessible_order
from app.services.payments.demo_khqr import get_provider
from app.services.store_settings import get_store_settings
from app.utils.time import utcnow

logger = logging.getLogger("campuseats.payments")


def checkout_out(order: Order, payment: Payment) -> PaymentCheckoutOut:
    provider = get_provider(payment.provider)
    data = provider.create_checkout(order, payment)
    out = PaymentCheckoutOut.model_validate(payment)
    if payment.status == PaymentStatus.PENDING:
        out.qr_payload = data.qr_payload
    out.is_demo = data.is_demo
    return out


def status_out(order: Order, payment: Payment) -> PaymentStatusOut:
    return PaymentStatusOut(
        payment_id=payment.id,
        order_id=order.id,
        order_number=order.order_number,
        status=payment.status,
        order_status=order.status,
        amount=payment.amount,
        currency=payment.currency,
        expires_at=payment.expires_at,
        paid_at=payment.paid_at,
        transaction_reference=payment.transaction_reference,
    )


def require_demo_mode() -> None:
    if not settings.demo_payments_enabled or settings.app_env == "production":
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "DEMO_DISABLED",
            "Demo payments are disabled on this server.",
        )


async def get_or_create_checkout(
    session: AsyncSession, order_id: uuid.UUID, user: User | None, guest_token: str | None
) -> PaymentCheckoutOut:
    """Return the order's open payment, creating one if none exists yet (idempotent)."""
    order = await get_accessible_order(session, order_id, user, guest_token)
    await expire_if_due(session, order)

    latest = order.latest_payment
    if order.status != OrderStatus.PENDING_PAYMENT:
        if latest is None:
            raise conflict("ORDER_NOT_PAYABLE", "This order cannot be paid.")
        return checkout_out(order, latest)
    if latest is not None and latest.status == PaymentStatus.PENDING:
        return checkout_out(order, latest)

    locked = await get_accessible_order(session, order_id, user, guest_token, for_update=True)
    open_payment = next((p for p in locked.payments if p.status == PaymentStatus.PENDING), None)
    if open_payment is None:
        store = await get_store_settings(session)
        open_payment = Payment(
            order_id=locked.id,
            provider=get_provider().name,
            amount=locked.total,
            currency="USD",
            status=PaymentStatus.PENDING,
            expires_at=utcnow() + timedelta(minutes=store.payment_expiry_minutes),
        )
        session.add(open_payment)
    await session.commit()
    return checkout_out(locked, open_payment)


async def confirm_payment(
    session: AsyncSession,
    *,
    order_id: uuid.UUID,
    payment_id: uuid.UUID,
    user: User | None,
    guest_token: str | None,
) -> DemoConfirmOut:
    # 1. Lock the order (proves the caller may act on it), then the payment.
    order = await get_accessible_order(session, order_id, user, guest_token, for_update=True)
    payment = await session.scalar(
        select(Payment)
        .where(Payment.id == payment_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    # 2. The payment must belong to this exact order.
    if payment is None or payment.order_id != order.id:
        raise not_found("Payment")

    # 3. Idempotency: a repeated confirmation returns the original result.
    if payment.status == PaymentStatus.PAID:
        return DemoConfirmOut(**status_out(order, payment).model_dump(), already_confirmed=True)

    if payment.status != PaymentStatus.PENDING:
        raise conflict(
            "PAYMENT_NOT_PENDING", f"This payment is {payment.status.value} and cannot be paid."
        )

    # 4. Expired? Close the order and release its stock instead.
    if payment.expires_at <= utcnow():
        if order.status == OrderStatus.PENDING_PAYMENT:
            await cancel_locked_order(session, order, "Payment window expired", expired=True)
        else:
            payment.status = PaymentStatus.EXPIRED
        await session.commit()
        raise conflict("PAYMENT_EXPIRED", "This payment has expired. Please place a new order.")

    if order.status != OrderStatus.PENDING_PAYMENT:
        raise conflict("ORDER_NOT_PAYABLE", f"This order is {order.status.value}.")

    # 5. Defensive amount check against the authoritative order total.
    if payment.amount != order.total or payment.currency != "USD":
        raise conflict("AMOUNT_MISMATCH", "Payment amount does not match the order total.")

    provider = get_provider(payment.provider)
    payment.status = PaymentStatus.PAID
    payment.paid_at = utcnow()
    payment.transaction_reference = provider.new_transaction_reference(payment)
    order.status = OrderStatus.CONFIRMED
    await session.commit()
    logger.info("Payment %s confirmed for order %s", payment.id, order.order_number)
    return DemoConfirmOut(**status_out(order, payment).model_dump(), already_confirmed=False)


async def get_payment_status(
    session: AsyncSession, payment_id: uuid.UUID, user: User | None, guest_token: str | None
) -> PaymentStatusOut:
    payment = await session.get(Payment, payment_id)
    if payment is None:
        raise not_found("Payment")
    order = await get_accessible_order(session, payment.order_id, user, guest_token)
    if await expire_if_due(session, order):
        await session.refresh(payment)
    return status_out(order, payment)
