import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import InventoryReason


class InventoryMovement(Base):
    """Append-only stock ledger. Every change to `foods.stock_quantity` writes a row here."""

    __tablename__ = "inventory_movements"
    __table_args__ = (
        CheckConstraint("quantity_change <> 0", name="change_non_zero"),
        # An order can reserve (and release) each food at most once: this makes
        # double-restoring stock impossible at the database level.
        Index(
            "uq_inventory_movements_order_food_reason",
            "order_id",
            "food_id",
            "reason",
            unique=True,
            postgresql_where=text("order_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"), index=True)
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), index=True
    )
    quantity_change: Mapped[int] = mapped_column(Integer)
    reason: Mapped[InventoryReason] = mapped_column(
        Enum(
            InventoryReason,
            native_enum=False,
            length=30,
            values_callable=lambda e: [m.value for m in e],
            validate_strings=True,
            create_constraint=True,
            name="inventory_reason",
        ),
    )
    note: Mapped[str | None] = mapped_column(String(300))
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
