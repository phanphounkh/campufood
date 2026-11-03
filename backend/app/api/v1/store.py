from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import SessionDep
from app.core.config import settings
from app.schemas.admin import PublicSettings
from app.services.store_settings import get_store_settings

router = APIRouter(tags=["store"])


@router.get("/settings", response_model=PublicSettings, summary="Public canteen information")
async def public_settings(session: SessionDep) -> PublicSettings:
    store = await get_store_settings(session)
    return PublicSettings(
        **store.model_dump(),
        demo_payments_enabled=settings.demo_payments_enabled and settings.app_env != "production",
        timezone=settings.timezone,
    )


@router.get("/health", summary="Liveness and database connectivity")
async def health(session: SessionDep) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
