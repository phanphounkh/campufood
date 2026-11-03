"""Password hashing, JWT session tokens, CSRF tokens and guest order tokens."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

# Argon2id with pwdlib's recommended parameters.
password_hasher = PasswordHash.recommended()

# Used to equalise timing when a login email does not exist.
_DUMMY_HASH = password_hasher.hash("campuseats-timing-equaliser")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        password_hasher.verify(password, _DUMMY_HASH)
        return False
    try:
        return password_hasher.verify(password, password_hash)
    except Exception:
        return False


def create_access_token(user_id: int, role: str) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "exp": expires_at,
        "iat": datetime.now(UTC),
        "jti": secrets.token_hex(8),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp"]},
        )
    except jwt.PyJWTError:
        return None


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def tokens_match(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    return hmac.compare_digest(a.encode(), b.encode())


def new_guest_token() -> str:
    """Unguessable secret handed to a guest once, at order creation."""
    return secrets.token_urlsafe(32)


def hash_guest_token(token: str) -> str:
    # Tokens carry 256 bits of entropy, so a fast hash is appropriate (no brute force risk).
    return hashlib.sha256(token.encode()).hexdigest()
