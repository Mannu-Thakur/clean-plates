"""
JWT authentication dependencies.

- ``get_current_user``: standard JWT bearer dependency for protected routes.
- ``get_current_user_optional``: for WebSocket (token in query param).
- ``get_api_key_device``: for ML pipeline routes.

Ref: 04-middlewares.md §1, §11
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, hash_token
from app.middleware.db import get_db_session
from app.models.user import UserModel
from app.schemas.auth import UserSchema

_bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> UserSchema:
    """Decode JWT from Authorization header, fetch user, return UserSchema."""
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
    """For WebSocket — extract token from query param, return user or None."""
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
    x_api_key: str = Depends(lambda: ""),  # Placeholder — replaced by Header dependency
    db: AsyncSession = Depends(get_db_session),
):
    """For ML pipeline routes — validates API key against device records.

    NOTE: Full implementation deferred to Phase 2 when DeviceModel exists.
    This stub is here to establish the dependency signature.
    """
    # Phase 2: hash the key and look up device
    # from app.models.device import DeviceModel
    # key_hash = hash_token(x_api_key)
    # result = await db.execute(select(DeviceModel).where(DeviceModel.api_key_hash == key_hash))
    # device = result.scalar_one_or_none()
    # if not device or device.is_deleted:
    #     raise HTTPException(status_code=401, detail="Invalid API key")
    # return device
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="API key auth will be available in Phase 2",
    )
