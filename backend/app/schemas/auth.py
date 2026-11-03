from datetime import datetime

import email_validator
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import UserRole
from app.schemas.common import Schema
from app.utils.text import normalize_phone

# Canteens often use internal addresses (e.g. admin@campuseats.local) for staff accounts.
if "local" in email_validator.SPECIAL_USE_DOMAIN_NAMES:
    email_validator.SPECIAL_USE_DOMAIN_NAMES.remove("local")


class LoginRequest(BaseModel):
    # Not strictly validated: it is only compared with existing accounts.
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+$")
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Name is too short")
        return v

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str | None) -> str | None:
        if not v:
            return None
        phone = normalize_phone(v)
        if not 8 <= len(phone.lstrip("+")) <= 15:
            raise ValueError("Enter a valid phone number")
        return phone


class UserOut(Schema):
    id: int
    name: str
    email: str
    phone: str | None
    role: UserRole
    is_active: bool
    created_at: datetime


class SessionOut(BaseModel):
    user: UserOut
    csrf_token: str
    expires_at: datetime


class StaffCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=10, max_length=128)
    role: UserRole = UserRole.STAFF

    @field_validator("role")
    @classmethod
    def staff_roles_only(cls, v: UserRole) -> UserRole:
        if v == UserRole.CUSTOMER:
            raise ValueError("Use registration for customer accounts")
        return v


class UserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None
