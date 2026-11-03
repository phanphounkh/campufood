import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import OrderStatus, PaymentStatus
from app.schemas.common import Money


class DemoPaymentCreate(BaseModel):
    order_id: uuid.UUID


class DemoPaymentConfirm(BaseModel):
    order_id: uuid.UUID
    payment_id: uuid.UUID


class PaymentStatusOut(BaseModel):
    payment_id: uuid.UUID
    order_id: uuid.UUID
    order_number: str
    status: PaymentStatus
    order_status: OrderStatus
    amount: Money
    currency: str
    expires_at: datetime
    paid_at: datetime | None
    transaction_reference: str | None


class DemoConfirmOut(PaymentStatusOut):
    already_confirmed: bool
