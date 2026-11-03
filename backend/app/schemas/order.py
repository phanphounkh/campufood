import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import OrderStatus, PaymentStatus
from app.schemas.common import Money, Schema
from app.utils.text import normalize_phone

MAX_ITEM_QUANTITY = 20
MAX_DISTINCT_ITEMS = 30


class OrderItemIn(BaseModel):
    food_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=MAX_ITEM_QUANTITY)


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=80)
    customer_phone: str = Field(min_length=6, max_length=32)
    student_id: str | None = Field(default=None, max_length=40)
    pickup_time: datetime
    notes: str | None = Field(default=None, max_length=300)
    items: list[OrderItemIn] = Field(min_length=1, max_length=MAX_DISTINCT_ITEMS)
    # Optional: what the customer saw. Never used for pricing — only to detect a stale
    # cart, in which case the API answers 409 PRICE_CHANGED instead of charging a surprise.
    expected_total: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)

    @field_validator("customer_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Please enter your name")
        return v

    @field_validator("customer_phone")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        if not all(c.isdigit() or c in " +-()." for c in v.strip()):
            raise ValueError("Phone number may only contain digits, spaces, +, - and ()")
        phone = normalize_phone(v)
        if not 8 <= len(phone.lstrip("+")) <= 15:
            raise ValueError("Enter a valid phone number")
        return phone

    @field_validator("student_id", "notes")
    @classmethod
    def blank_to_none(cls, v: str | None) -> str | None:
        v = v.strip() if v else v
        return v or None

    @field_validator("pickup_time")
    @classmethod
    def require_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("Pickup time must include a time zone")
        return v

    @model_validator(mode="after")
    def merge_duplicate_items(self) -> "OrderCreate":
        merged: dict[int, int] = {}
        for item in self.items:
            merged[item.food_id] = merged.get(item.food_id, 0) + item.quantity
        for food_id, qty in merged.items():
            if qty > MAX_ITEM_QUANTITY:
                raise ValueError(
                    f"At most {MAX_ITEM_QUANTITY} of one item per order (food {food_id})"
                )
        self.items = [OrderItemIn(food_id=f, quantity=q) for f, q in merged.items()]
        return self


class OrderItemOut(Schema):
    id: int
    food_id: int | None
    food_name_snapshot: str
    food_name_km_snapshot: str
    quantity: int
    unit_price: Money
    line_total: Money


class PaymentOut(Schema):
    id: uuid.UUID
    order_id: uuid.UUID
    provider: str
    amount: Money
    currency: str
    status: PaymentStatus
    transaction_reference: str | None
    expires_at: datetime
    paid_at: datetime | None
    refunded_at: datetime | None
    created_at: datetime


class PaymentCheckoutOut(PaymentOut):
    """A payment plus what the client needs to show a QR code."""

    qr_payload: str | None = None
    is_demo: bool = False


class OrderOut(Schema):
    id: uuid.UUID
    order_number: str
    user_id: int | None
    customer_name: str
    customer_phone: str
    student_id: str | None
    pickup_time: datetime
    notes: str | None
    subtotal: Money
    total: Money
    status: OrderStatus
    cancel_reason: str | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut]
    payment: PaymentOut | None = None

    @model_validator(mode="before")
    @classmethod
    def attach_latest_payment(cls, data: object) -> object:
        latest = getattr(data, "latest_payment", None)
        if latest is not None and not isinstance(data, dict):
            fields = {name: getattr(data, name) for name in cls.model_fields if name != "payment"}
            return {**fields, "payment": latest}
        return data


class OrderCreated(BaseModel):
    order: OrderOut
    payment: PaymentCheckoutOut
    # Shown once. The client stores it to view this order without an account.
    access_token: str


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    reason: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def reason_required_for_cancel(self) -> "OrderStatusUpdate":
        if self.status == OrderStatus.CANCELLED and not (self.reason and self.reason.strip()):
            raise ValueError("A reason is required to cancel an order")
        return self
