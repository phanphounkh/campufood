import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin
from app.models.enums import PaymentStatus
from app.models.order import Order


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        # At most one successful (or later refunded) payment per order: a hard guarantee
        # against double charging even if application-level checks were bypassed.
        Index(
            "uq_payments_one_success_per_order",
            "order_id",
            unique=True,
            postgresql_where=text("status IN ('paid', 'refunded')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(32))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD", server_default="USD")
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            PaymentStatus,
            native_enum=False,
            length=20,
            values_callable=lambda e: [m.value for m in e],
            validate_strings=True,
            create_constraint=True,
            name="payment_status",
        ),
        default=PaymentStatus.PENDING,
        index=True,
    )
    transaction_reference: Mapped[str | None] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    order: Mapped[Order] = relationship(back_populates="payments")
