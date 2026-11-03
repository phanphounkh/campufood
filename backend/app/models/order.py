import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Sequence,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.models.enums import OrderStatus

# Human-friendly, sequential order numbers (CE-1001, CE-1002 ...). These are display
# labels only; orders are looked up by UUID plus an access check, never by number alone.
order_number_seq = Sequence("order_number_seq", start=1001, metadata=Base.metadata)


class Order(TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="subtotal_non_negative"),
        CheckConstraint("total >= 0", name="total_non_negative"),
        Index("ix_orders_created_at", "created_at"),
    )
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        server_default=text("'CE-' || nextval('order_number_seq'::regclass)"),
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    guest_access_token_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    customer_phone: Mapped[str] = mapped_column(String(32), index=True)
    student_id: Mapped[str | None] = mapped_column(String(40))
    pickup_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(
            OrderStatus,
            native_enum=False,
            length=20,
            values_callable=lambda e: [m.value for m in e],
            validate_strings=True,
            create_constraint=True,
            name="order_status",
        ),
        default=OrderStatus.PENDING_PAYMENT,
        index=True,
    )
    cancel_reason: Mapped[str | None] = mapped_column(String(300))

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="OrderItem.id",
    )
    payments: Mapped[list["Payment"]] = relationship(  # noqa: F821
        back_populates="order",
        lazy="selectin",
        order_by="Payment.created_at",
    )

    @property
    def latest_payment(self) -> "Payment | None":  # noqa: F821
        return self.payments[-1] if self.payments else None


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_price >= 0", name="unit_price_non_negative"),
        UniqueConstraint("order_id", "food_id", name="uq_order_items_order_food"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    food_id: Mapped[int | None] = mapped_column(
        ForeignKey("foods.id", ondelete="SET NULL"), index=True
    )
    food_name_snapshot: Mapped[str] = mapped_column(String(120))
    food_name_km_snapshot: Mapped[str] = mapped_column(String(120), default="", server_default="")
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    line_total: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped[Order] = relationship(back_populates="items")
