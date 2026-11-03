"""Key/value store settings with typed defaults."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Setting
from app.schemas.admin import StoreSettings, StoreSettingsUpdate


async def get_store_settings(session: AsyncSession) -> StoreSettings:
    rows = (await session.execute(select(Setting.key, Setting.value))).all()
    stored: dict[str, Any] = {key: value for key, value in rows}
    known = {k: v for k, v in stored.items() if k in StoreSettings.model_fields}
    # Fall back to defaults for anything missing or no longer valid.
    try:
        return StoreSettings(**known)
    except ValueError:
        return StoreSettings()


async def update_store_settings(
    session: AsyncSession, changes: StoreSettingsUpdate
) -> StoreSettings:
    current = await get_store_settings(session)
    merged = current.model_dump() | changes.model_dump(exclude_unset=True, exclude_none=True)
    validated = StoreSettings(**merged)  # re-validate the combination (e.g. opening < closing)
    for key, value in validated.model_dump().items():
        stmt = insert(Setting).values(key=key, value=value)
        stmt = stmt.on_conflict_do_update(index_elements=[Setting.key], set_={"value": value})
        await session.execute(stmt)
    await session.commit()
    return validated
