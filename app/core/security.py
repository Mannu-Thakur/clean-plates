"""
Security utilities — password hashing, JWT token management.

⚠ P1-fix: bcrypt is intentionally slow (~100-300ms). hash_password and
verify_password are wrapped in asyncio.to_thread to avoid blocking the
ASGI event loop.

Ref: 06-phase-wise-plan.md Phase 1, Cross-Cutting Rule #14
"""

from __future__ import annotations

import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# ── Password hashing (bcrypt direct — passlib is broken with bcrypt>=4.1) ────
def _hash_sync(plain: str) -> str:
    """Synchronous bcrypt hash."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_sync(plain: str, hashed: str) -> bool:
    """Synchronous bcrypt verify."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


async def hash_password(plain: str) -> str:
    """Hash a password using bcrypt — runs in a thread to avoid event-loop blocking."""
    return await asyncio.to_thread(_hash_sync, plain)


async def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash — runs in a thread."""
    return await asyncio.to_thread(_verify_sync, plain, hashed)


# ── JWT token management ────────────────────────────────────────────────────
_ALGORITHM = "HS256"


def _utcnow() -> datetime:
    """Naive UTC now — required for SQLite datetime columns.

    SQLite stores datetimes as plain strings without timezone info.
    Using aware datetimes (timezone.utc) in comparisons against SQLite
    rows raises TypeError. Always use this for DB-bound values.
    """
    return datetime.utcnow()  # noqa: DTZ003


def create_access_token(user_id: str, role: str) -> tuple[str, int]:
    """Return (encoded_jwt, expires_in_seconds)."""
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # JWT exp uses aware datetime (jose library handles it correctly)
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)
    return token, int(expires_delta.total_seconds())


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    """Return (encoded_jwt, expires_at_naive_utc).

    expires_at is naive UTC for direct SQLite storage.
    """
    expires_at_naive = _utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    # JWT uses aware datetime internally
    expires_at_aware = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": secrets.token_hex(16),
        "exp": expires_at_aware,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)
    return token, expires_at_naive  # naive — safe to store in SQLite


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT. Returns the payload dict or None on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """SHA-256 hash of a token for secure DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_reset_token() -> tuple[str, str]:
    """Return (raw_token, hashed_token) for password resets."""
    raw = secrets.token_urlsafe(32)
    hashed = hash_token(raw)
    return raw, hashed


def generate_api_key() -> tuple[str, str]:
    """Return (raw_api_key, hashed_api_key) for device registration."""
    raw = f"cp_{secrets.token_hex(32)}"
    hashed = hash_token(raw)
    return raw, hashed
