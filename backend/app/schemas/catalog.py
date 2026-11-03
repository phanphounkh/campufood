import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, BaseModel, BeforeValidator, Field, field_validator

from app.core.config import settings
from app.schemas.common import Money, Schema

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MEDIA_PATH_RE = re.compile(r"^/media/[A-Za-z0-9/_.-]+\.(?:webp|jpe?g|png)$")


def _collapse_spaces(v: object) -> object:
    return " ".join(v.split()) if isinstance(v, str) else v


def _strip(v: object) -> object:
    return v.strip() if isinstance(v, str) else v


CleanStr = Annotated[str, BeforeValidator(_collapse_spaces)]
CleanText = Annotated[str, BeforeValidator(_strip)]


def validate_image_url(v: str | None) -> str | None:
    if v is None or v == "":
        return None
    if v.startswith(settings.media_url_prefix + "/"):
        if ".." in v or not MEDIA_PATH_RE.match(v):
            raise ValueError("Invalid media path")
        return v
    if re.match(r"^https://[^\s\"'<>]+$", v):
        return v
    raise ValueError("Image must be an uploaded file or an https:// URL")


ImageUrl = Annotated[str | None, AfterValidator(validate_image_url)]


# ── Categories ─────────────────────────────────────────────────


class CategoryBrief(Schema):
    id: int
    slug: str
    name_en: str
    name_km: str


class CategoryOut(CategoryBrief):
    sort_order: int
    created_at: datetime
    food_count: int = 0


class CategoryCreate(BaseModel):
    name_en: CleanStr = Field(min_length=1, max_length=80)
    name_km: CleanStr = Field(min_length=1, max_length=80)
    slug: str | None = Field(default=None, max_length=80)
    sort_order: int = Field(default=0, ge=0, le=1000)

    @field_validator("slug")
    @classmethod
    def check_slug(cls, v: str | None) -> str | None:
        if v is not None and v != "" and not SLUG_RE.match(v):
            raise ValueError("Slug may contain lowercase letters, numbers and dashes only")
        return v or None


class CategoryUpdate(BaseModel):
    name_en: CleanStr | None = Field(default=None, min_length=1, max_length=80)
    name_km: CleanStr | None = Field(default=None, min_length=1, max_length=80)
    slug: str | None = Field(default=None, min_length=1, max_length=80)
    sort_order: int | None = Field(default=None, ge=0, le=1000)

    @field_validator("slug")
    @classmethod
    def check_slug(cls, v: str | None) -> str | None:
        if v is not None and not SLUG_RE.match(v):
            raise ValueError("Slug may contain lowercase letters, numbers and dashes only")
        return v


# ── Foods ──────────────────────────────────────────────────────

Price = Annotated[
    Decimal, Field(gt=Decimal("0"), le=Decimal("1000"), max_digits=8, decimal_places=2)
]


class FoodOut(Schema):
    id: int
    category_id: int
    category: CategoryBrief
    name_en: str
    name_km: str
    description_en: str
    description_km: str
    price: Money
    image_url: str | None
    stock_quantity: int
    is_available: bool
    is_featured: bool
    is_archived: bool
    is_sold_out: bool
    created_at: datetime
    updated_at: datetime


class FoodCreate(BaseModel):
    category_id: int = Field(gt=0)
    name_en: CleanStr = Field(min_length=1, max_length=120)
    name_km: CleanStr = Field(min_length=1, max_length=120)
    description_en: CleanText = Field(default="", max_length=500)
    description_km: CleanText = Field(default="", max_length=500)
    price: Price
    image_url: ImageUrl = Field(default=None, max_length=500)
    stock_quantity: int = Field(default=0, ge=0, le=100_000)
    is_available: bool = True
    is_featured: bool = False


class FoodUpdate(BaseModel):
    category_id: int | None = Field(default=None, gt=0)
    name_en: CleanStr | None = Field(default=None, min_length=1, max_length=120)
    name_km: CleanStr | None = Field(default=None, min_length=1, max_length=120)
    description_en: CleanText | None = Field(default=None, max_length=500)
    description_km: CleanText | None = Field(default=None, max_length=500)
    price: Price | None = None
    image_url: ImageUrl = Field(default=None, max_length=500)
    stock_quantity: int | None = Field(default=None, ge=0, le=100_000)
    is_available: bool | None = None
    is_featured: bool | None = None
    is_archived: bool | None = None
