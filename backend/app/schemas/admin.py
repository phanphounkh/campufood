import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import InventoryReason, OrderStatus, PaymentStatus
from app.schemas.common import Money, Schema

# ── Dashboard ──────────────────────────────────────────────────


class KpiValue(BaseModel):
    value: int | Money
    previous: int | Money
    change_pct: float | None


class TimePoint(BaseModel):
    label: str
    start: datetime
    orders: int
    revenue: Money


class StatusCount(BaseModel):
    status: OrderStatus
    count: int


class PopularItem(BaseModel):
    food_id: int | None
    name_en: str
    name_km: str
    image_url: str | None
    quantity: int
    revenue: Money


class RecentOrder(BaseModel):
    id: uuid.UUID
    order_number: str
    customer_name: str
    item_count: int
    items_summary: str
    total: Money
    payment_status: PaymentStatus | None
    status: OrderStatus
    created_at: datetime


class DashboardOut(BaseModel):
    range: Literal["today", "7d", "30d"]
    generated_at: datetime
    total_orders: KpiValue
    revenue: KpiValue
    completed_orders: KpiValue
    average_order_value: KpiValue
    pending_orders: int
    in_progress_orders: int
    awaiting_payment: int
    low_stock_count: int
    sales_over_time: list[TimePoint]
    daily_revenue: list[TimePoint]
    orders_by_status: list[StatusCount]
    popular_items: list[PopularItem]
    recent_orders: list[RecentOrder]


# ── Reports ────────────────────────────────────────────────────


class ReportPeriod(BaseModel):
    period: str
    start: date
    orders: int
    items_sold: int
    gross_sales: Money
    refunds: Money
    net_revenue: Money
    cancelled_orders: int


class ReportTotals(BaseModel):
    orders: int
    items_sold: int
    gross_sales: Money
    refunds: Money
    net_revenue: Money
    cancelled_orders: int
    refunded_orders: int
    average_order_value: Money


class ReportOut(BaseModel):
    date_from: date
    date_to: date
    granularity: Literal["day", "week", "month"]
    totals: ReportTotals
    periods: list[ReportPeriod]
    best_sellers: list[PopularItem]


# ── Inventory ──────────────────────────────────────────────────


class InventoryItem(Schema):
    food_id: int
    name_en: str
    name_km: str
    category_name_en: str
    image_url: str | None
    stock_quantity: int
    is_available: bool
    low_stock: bool
    reserved_quantity: int
    updated_at: datetime


class InventoryUpdate(BaseModel):
    mode: Literal["set", "adjust"] = "adjust"
    quantity: int = Field(ge=-100_000, le=100_000)
    reason: Literal[InventoryReason.RESTOCK, InventoryReason.MANUAL_ADJUSTMENT] = (
        InventoryReason.RESTOCK
    )
    note: str | None = Field(default=None, max_length=300)
    is_available: bool | None = None

    @field_validator("quantity")
    @classmethod
    def check_set_value(cls, v: int, info) -> int:
        if info.data.get("mode") == "set" and v < 0:
            raise ValueError("Stock cannot be negative")
        return v


class InventoryMovementOut(Schema):
    id: int
    food_id: int
    food_name_en: str
    order_id: uuid.UUID | None
    order_number: str | None
    quantity_change: int
    reason: InventoryReason
    note: str | None
    created_at: datetime


# ── Customers & payments ───────────────────────────────────────


class CustomerOut(BaseModel):
    customer_phone: str
    customer_name: str
    is_registered: bool
    email: str | None
    orders_count: int
    paid_orders: int
    total_spent: Money
    first_order_at: datetime
    last_order_at: datetime


class AdminPaymentOut(Schema):
    id: uuid.UUID
    order_id: uuid.UUID
    order_number: str
    customer_name: str
    provider: str
    amount: Money
    currency: str
    status: PaymentStatus
    transaction_reference: str | None
    expires_at: datetime
    paid_at: datetime | None
    refunded_at: datetime | None
    created_at: datetime


class PaymentSummary(BaseModel):
    collected: Money
    refunded: Money
    pending: Money
    count_by_status: dict[str, int]


# ── Settings ───────────────────────────────────────────────────

HHMM = r"^([01]\d|2[0-3]):[0-5]\d$"


class StoreSettings(BaseModel):
    store_name: str = Field(default="CampusEats", min_length=1, max_length=80)
    store_tagline: str = Field(default="Student Canteen", max_length=120)
    store_phone: str = Field(default="", max_length=40)
    store_email: str = Field(default="", max_length=120)
    store_address: str = Field(default="", max_length=200)
    opening_time: str = Field(default="07:00", pattern=HHMM)
    closing_time: str = Field(default="17:00", pattern=HHMM)
    accepting_orders: bool = True
    min_prep_minutes: int = Field(default=15, ge=0, le=240)
    payment_expiry_minutes: int = Field(default=15, ge=2, le=120)
    low_stock_threshold: int = Field(default=10, ge=0, le=10_000)
    facebook_url: str = Field(default="", max_length=200)
    telegram_url: str = Field(default="", max_length=200)
    instagram_url: str = Field(default="", max_length=200)

    @field_validator("facebook_url", "telegram_url", "instagram_url")
    @classmethod
    def https_only(cls, v: str) -> str:
        if v and not v.startswith("https://"):
            raise ValueError("Links must start with https://")
        return v

    @field_validator("closing_time")
    @classmethod
    def closes_after_opening(cls, v: str, info) -> str:
        opening = info.data.get("opening_time")
        if opening and v <= opening:
            raise ValueError("Closing time must be after opening time")
        return v


class StoreSettingsUpdate(BaseModel):
    store_name: str | None = Field(default=None, min_length=1, max_length=80)
    store_tagline: str | None = Field(default=None, max_length=120)
    store_phone: str | None = Field(default=None, max_length=40)
    store_email: str | None = Field(default=None, max_length=120)
    store_address: str | None = Field(default=None, max_length=200)
    opening_time: str | None = Field(default=None, pattern=HHMM)
    closing_time: str | None = Field(default=None, pattern=HHMM)
    accepting_orders: bool | None = None
    min_prep_minutes: int | None = Field(default=None, ge=0, le=240)
    payment_expiry_minutes: int | None = Field(default=None, ge=2, le=120)
    low_stock_threshold: int | None = Field(default=None, ge=0, le=10_000)
    facebook_url: str | None = Field(default=None, max_length=200)
    telegram_url: str | None = Field(default=None, max_length=200)
    instagram_url: str | None = Field(default=None, max_length=200)


class PublicSettings(StoreSettings):
    demo_payments_enabled: bool
    timezone: str
    currency: str = "USD"


class UploadOut(BaseModel):
    url: str
    width: int
    height: int
    size_bytes: int
