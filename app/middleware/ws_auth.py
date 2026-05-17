"""
WebSocket authentication dependencies.

JWTs are supplied through ``?token=<access_jwt>`` because browsers cannot set
custom Authorization headers during the WebSocket upgrade.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, WebSocket, WebSocketException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.middleware.db import get_db_session
from app.models.user import UserModel
from app.schemas.auth import UserSchema

WS_UNAUTHORIZED_CODE = 4001
WS_FORBIDDEN_CODE = 4003


def _token_from_websocket(websocket: WebSocket) -> str | None:
    token = websocket.query_params.get("token")
    if token:
        return token

    authorization = websocket.headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", maxsplit=1)[1].strip()
    return None


async def get_current_ws_user(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db_session),
) -> UserSchema:
    """Validate the WebSocket JWT and return the active user."""
    token = _token_from_websocket(websocket)
    if not token:
        raise WebSocketException(code=WS_UNAUTHORIZED_CODE, reason="Missing token")

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise WebSocketException(code=WS_UNAUTHORIZED_CODE, reason="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise WebSocketException(code=WS_UNAUTHORIZED_CODE, reason="Invalid token payload")

    result = await db.execute(select(UserModel).where(UserModel.id == str(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise WebSocketException(code=WS_UNAUTHORIZED_CODE, reason="User not found or inactive")

    return UserSchema.model_validate(user)


def require_ws_roles(*roles: str) -> Callable:
    """Return a WebSocket dependency that enforces role membership."""

    async def _check(current_user: UserSchema = Depends(get_current_ws_user)) -> UserSchema:
        if current_user.role not in roles:
            raise WebSocketException(code=WS_FORBIDDEN_CODE, reason="Role does not have access to this stream")
        return current_user

    return _check
