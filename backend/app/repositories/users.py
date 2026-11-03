from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(func.lower(User.email) == email.lower()))


async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)
