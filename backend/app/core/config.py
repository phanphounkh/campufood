"""Application settings loaded from environment variables (and the repo-level `.env`)."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent

WEAK_SECRETS = {"", "change-me", "change-me-to-a-long-random-string-of-at-least-32-chars"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "CampusEats API"
    app_env: Literal["development", "test", "production"] = "development"

    database_url: str = "postgresql+psycopg://campuseats:campuseats@localhost:5432/campuseats"
    test_database_url: str | None = None
    db_echo: bool = False

    jwt_secret: str = "change-me"  # noqa: S105  (dev default; rejected in production)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = Field(default=720, ge=5, le=60 * 24 * 14)

    session_cookie_name: str = "ce_session"
    csrf_cookie_name: str = "ce_csrf"
    csrf_header_name: str = "X-CSRF-Token"
    cookie_secure: bool = False

    allowed_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173","http://192.168.3.202:5173/"]
    trust_proxy_headers: bool = False

    demo_payments_enabled: bool = True

    media_root: Path = BACKEND_DIR / "media"
    media_url_prefix: str = "/media"
    max_upload_mb: int = Field(default=5, ge=1, le=20)

    # Background job that expires unpaid orders and releases reserved stock.
    expiry_sweep_seconds: int = Field(default=30, ge=5)
    run_background_jobs: bool = True

    # Canteen time zone, used for "today" and report grouping.
    timezone: str = "Asia/Phnom_Penh"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [o.strip().rstrip("/") for o in value.split(",") if o.strip()]
        return value

    @field_validator("media_root", mode="after")
    @classmethod
    def resolve_media_root(cls, value: Path) -> Path:
        return value if value.is_absolute() else (BACKEND_DIR / value).resolve()

    @model_validator(mode="after")
    def check_production_safety(self) -> "Settings":
        if self.app_env == "production":
            if self.jwt_secret in WEAK_SECRETS or len(self.jwt_secret) < 32:
                raise ValueError("JWT_SECRET must be a random string of at least 32 characters")
            if not self.cookie_secure:
                raise ValueError("COOKIE_SECURE must be true in production")
        return self

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
