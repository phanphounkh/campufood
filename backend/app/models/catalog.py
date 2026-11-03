from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_en: Mapped[str] = mapped_column(String(80))
    name_km: Mapped[str] = mapped_column(String(80))
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Food(TimestampMixin, Base):
    __tablename__ = "foods"
    __table_args__ = (
        CheckConstraint("price > 0", name="price_positive"),
        CheckConstraint("stock_quantity >= 0", name="stock_non_negative"),
        Index("ix_foods_listing", "is_archived", "is_available", "category_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True
    )
    name_en: Mapped[str] = mapped_column(String(120))
    name_km: Mapped[str] = mapped_column(String(120))
    description_en: Mapped[str] = mapped_column(Text, default="", server_default="")
    description_km: Mapped[str] = mapped_column(Text, default="", server_default="")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    image_url: Mapped[str | None] = mapped_column(String(500))
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    category: Mapped[Category] = relationship(lazy="joined")

    @property
    def is_sold_out(self) -> bool:
        return self.stock_quantity <= 0 or not self.is_available
