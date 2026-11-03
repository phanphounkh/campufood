from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin
from app.models.enums import UserRole


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            native_enum=False,
            length=20,
            values_callable=lambda e: [m.value for m in e],
            validate_strings=True,
            create_constraint=True,
            name="user_role",
        ),
        default=UserRole.CUSTOMER,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    @property
    def is_staff(self) -> bool:
        return self.role in (UserRole.ADMIN, UserRole.STAFF)
