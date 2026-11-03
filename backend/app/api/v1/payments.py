import uuid

from fastapi import APIRouter, Depends

from app.api.deps import GuestToken, OptionalUser, SessionDep
from app.core.rate_limit import rate_limit
from app.schemas.order import PaymentCheckoutOut
from app.schemas.payment import (
    DemoConfirmOut,
    DemoPaymentConfirm,
    DemoPaymentCreate,
    PaymentStatusOut,
)
from app.services.payments import service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "/demo/create",
    response_model=PaymentCheckoutOut,
    dependencies=[Depends(rate_limit("payment_create", 30, 60))],
    summary="Get (or open) the demo KHQR payment for an order you own",
)
async def create_demo_payment(
    data: DemoPaymentCreate, session: SessionDep, user: OptionalUser, token: GuestToken = None
) -> PaymentCheckoutOut:
    return await service.get_or_create_checkout(session, data.order_id, user, token)


@router.post(
    "/demo/confirm",
    response_model=DemoConfirmOut,
    dependencies=[
        Depends(service.require_demo_mode),
        Depends(rate_limit("payment_confirm", 20, 60)),
    ],
    summary="Simulate a successful payment (demo mode only, idempotent)",
    description=(
        "Only available when DEMO_PAYMENTS_ENABLED=true. The caller must own the order "
        "(session or X-Order-Token) and the payment must belong to that order. Repeating the "
        "call returns the original confirmation without side effects."
    ),
)
async def confirm_demo_payment(
    data: DemoPaymentConfirm, session: SessionDep, user: OptionalUser, token: GuestToken = None
) -> DemoConfirmOut:
    return await service.confirm_payment(
        session, order_id=data.order_id, payment_id=data.payment_id, user=user, guest_token=token
    )


@router.get("/{payment_id}/status", response_model=PaymentStatusOut)
async def payment_status(
    payment_id: uuid.UUID, session: SessionDep, user: OptionalUser, token: GuestToken = None
) -> PaymentStatusOut:
    return await service.get_payment_status(session, payment_id, user, token)
