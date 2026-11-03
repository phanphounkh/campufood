from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, OptionalUser, SessionDep
from app.core.config import settings
from app.core.errors import AppError, conflict
from app.core.rate_limit import rate_limit
from app.core.security import create_access_token, hash_password, new_csrf_token, verify_password
from app.models import User, UserRole
from app.repositories.users import get_by_email
from app.schemas.auth import LoginRequest, RegisterRequest, SessionOut, UserOut
from app.schemas.common import Message

router = APIRouter(prefix="/auth", tags=["auth"])


class StaffLoginRequest(LoginRequest):
    # Set by the admin login form: refuse customer accounts before issuing a session.
    require_staff: bool = False


def _set_session(response: Response, user: User) -> SessionOut:
    token, expires_at = create_access_token(user.id, user.role.value)
    csrf = new_csrf_token()
    max_age = settings.jwt_expire_minutes * 60
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    # Readable by the web app so it can echo it in the X-CSRF-Token header (double submit).
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf,
        max_age=max_age,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return SessionOut(user=UserOut.model_validate(user), csrf_token=csrf, expires_at=expires_at)


def _clear_session(response: Response) -> None:
    for name in (settings.session_cookie_name, settings.csrf_cookie_name):
        response.delete_cookie(name, path="/", secure=settings.cookie_secure, samesite="lax")


@router.post(
    "/login",
    response_model=SessionOut,
    dependencies=[Depends(rate_limit("login", 10, 60))],
    summary="Log in with email and password (sets an HTTP-only session cookie)",
)
async def login(data: StaffLoginRequest, response: Response, session: SessionDep) -> SessionOut:
    user = await get_by_email(session, data.email)
    valid = verify_password(data.password, user.password_hash if user else None)
    if user is None or not valid or not user.is_active:
        raise AppError(
            status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS", "Incorrect email or password."
        )
    if data.require_staff and not user.is_staff:
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "FORBIDDEN",
            "This account does not have access to the admin area.",
        )
    return _set_session(response, user)


@router.post(
    "/register",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("register", 5, 300))],
    summary="Create a customer account (optional — guests can order without one)",
)
async def register(data: RegisterRequest, response: Response, session: SessionDep) -> SessionOut:
    if await get_by_email(session, data.email):
        raise conflict("EMAIL_TAKEN", "An account with this email already exists.")
    user = User(
        name=data.name,
        email=data.email.lower(),
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=UserRole.CUSTOMER,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise conflict("EMAIL_TAKEN", "An account with this email already exists.") from exc
    await session.refresh(user)
    return _set_session(response, user)


@router.post("/logout", response_model=Message)
async def logout(response: Response, _: OptionalUser) -> Message:
    _clear_session(response)
    return Message(message="Logged out")


@router.get("/me", response_model=UserOut, summary="The currently logged-in user")
async def me(user: CurrentUser) -> User:
    return user
