"""
Authentication primitives: password hashing (bcrypt) and JWT access/refresh tokens.

Security choices:
- Passwords hashed with bcrypt via passlib (never stored in plaintext).
- JWTs are signed with HS256 using ``SECRET_KEY`` and carry an explicit ``type``
  claim so an access token can never be used where a refresh token is expected.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except ValueError:
        return False


def _create_token(subject: str, token_type: TokenType, expires_minutes: int) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str) -> str:
    return _create_token(subject, "access", settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def create_refresh_token(subject: str) -> str:
    return _create_token(subject, "refresh", settings.REFRESH_TOKEN_EXPIRE_MINUTES)


def decode_token(token: str, expected_type: TokenType) -> str | None:
    """Return the subject (user id) if the token is valid and of the expected type."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload.get("sub")
