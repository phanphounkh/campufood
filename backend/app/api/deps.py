"""Shared FastAPI dependencies: DB session, current user, role guards, guest order token."""

from typing import Annotated

from fastapi import Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.models import User, UserRole

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(request: Request, session: SessionDep) -> User | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        return None
    # Always re-read the user: role changes and deactivation take effect immediately.
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user


OptionalUser = Annotated[User | None, Depends(get_current_user)]


def _unauthorized() -> AppError:
    return AppError(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", "Please log in to continue.")


def _forbidden() -> AppError:
    return AppError(
        status.HTTP_403_FORBIDDEN, "FORBIDDEN", "You do not have permission to do that."
    )


async def require_user(user: OptionalUser) -> User:
    if user is None:
        raise _unauthorized()
    return user


async def require_staff(user: OptionalUser) -> User:
    if user is None:
        raise _unauthorized()
    if user.role not in (UserRole.ADMIN, UserRole.STAFF):
        raise _forbidden()
    return user


async def require_admin(user: OptionalUser) -> User:
    if user is None:
        raise _unauthorized()
    if user.role != UserRole.ADMIN:
        raise _forbidden()
    return user


CurrentUser = Annotated[User, Depends(require_user)]
StaffUser = Annotated[User, Depends(require_staff)]
AdminUser = Annotated[User, Depends(require_admin)]

# Guests prove access to their order with the secret token issued at checkout.
GuestToken = Annotated[
    str | None,
    Header(
        alias="X-Order-Token",
        max_length=128,
        description="Guest order access token returned when the order was created.",
    ),
]
