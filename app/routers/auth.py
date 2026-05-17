"""
Auth router — all 6 auth routes.

Ref: 03-routes.md §1 — Prefix: /auth
"""

from __future__ import annotations

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, Request

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_arq_pool
from app.middleware.auth import get_current_user
from app.middleware.db import get_db_session
from app.schemas.auth import (
    ForgotPasswordSchema,
    LoginResponseSchema,
    LoginSchema,
    RefreshTokenSchema,
    ResetPasswordSchema,
    TokenPairSchema,
    UserSchema,
)
from app.schemas.common import MessageSchema
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponseSchema)
async def login(body: LoginSchema, request: Request, db: AsyncSession = Depends(get_db_session)):
    """Authenticate user and return JWT pair."""
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return await auth_service.authenticate(
        db, email=body.email, password=body.password,
        remember_me=body.remember_me, ip_address=ip, user_agent=ua,
    )


@router.post("/logout", response_model=MessageSchema)
async def logout(
    body: RefreshTokenSchema,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Revoke refresh token."""
    await auth_service.revoke_token(db, body.refresh_token, current_user.id)
    return MessageSchema(message="Logged out successfully")


@router.post("/refresh", response_model=TokenPairSchema)
async def refresh_token(body: RefreshTokenSchema, db: AsyncSession = Depends(get_db_session)):
    """Exchange refresh token for a new access token."""
    return await auth_service.refresh_tokens(db, body.refresh_token)


@router.get("/me", response_model=UserSchema)
async def get_me(current_user: UserSchema = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@router.post("/forgot-password", response_model=MessageSchema)
async def forgot_password(
    body: ForgotPasswordSchema,
    db: AsyncSession = Depends(get_db_session),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
):
    """Send password reset email."""
    await auth_service.request_password_reset(db, body.email, arq_pool=arq_pool)
    return MessageSchema(message="If that email exists, a reset link has been sent")


@router.post("/reset-password", response_model=MessageSchema)
async def reset_password(body: ResetPasswordSchema, db: AsyncSession = Depends(get_db_session)):
    """Set new password via reset token."""
    await auth_service.reset_password(db, body.token, body.new_password)
    return MessageSchema(message="Password has been reset successfully")
