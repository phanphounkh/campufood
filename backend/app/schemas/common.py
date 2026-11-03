from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer

from app.utils.money import to_money

# Money is exchanged as a fixed 2-decimal string ("1.50") so no client ever has to
# round-trip authoritative amounts through floating point.
Money = Annotated[
    Decimal, PlainSerializer(lambda v: str(to_money(v)), return_type=str, when_used="json")
]


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: object | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class Message(BaseModel):
    message: str
