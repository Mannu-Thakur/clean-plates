"""
JWT and API-key authentication dependencies.

- get_current_user: standard JWT bearer dependency for protected routes.
- get_current_user_optional: for WebSocket token lookup.
- get_api_key_device: validates edge-device API keys.
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, hash_token
from app.middleware.db import get_db_session
from app.models.user import UserModel
from app.schemas.auth import UserSchema

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> UserSchema:
    """Decode JWT from Authorization header, fetch user, return UserSchema."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return UserSchema.model_validate(user)


async def get_current_user_optional(
    token: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> UserSchema | None:
    """For WebSocket auth - extract token from query param, return user or None."""
    if not token:
        return None

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return None

    return UserSchema.model_validate(user)


async def get_api_key_device(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db_session),
):
    """Validate an edge API key and return the matching active DeviceModel."""
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    from app.models.device import DeviceModel

    key_hash = hash_token(x_api_key)
    result = await db.execute(select(DeviceModel).where(DeviceModel.api_key_hash == key_hash))
    device = result.scalar_one_or_none()
    if device is None or device.is_deleted or device.status == "decommissioned":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return device
