"""
Auth controller — thin layer dispatching to auth_service.

Ref: 02-controllers.md §1
"""

from __future__ import annotations

from arq.connections import ArqRedis
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import (
    ForgotPasswordSchema,
    LoginResponseSchema,
    LoginSchema,
    ResetPasswordSchema,
    TokenPairSchema,
    UserSchema,
)
from app.services import auth_service


async def login(body: LoginSchema, request: Request, db: AsyncSession) -> LoginResponseSchema:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return await auth_service.authenticate(
        db, email=body.email, password=body.password,
        remember_me=body.remember_me, ip_address=ip, user_agent=ua,
    )


async def logout(refresh_token: str, current_user: UserSchema, db: AsyncSession) -> None:
    await auth_service.revoke_token(db, refresh_token, current_user.id)


async def refresh_token(refresh_token_str: str, db: AsyncSession) -> TokenPairSchema:
    return await auth_service.refresh_tokens(db, refresh_token_str)


async def get_me(current_user: UserSchema) -> UserSchema:
    return current_user


async def forgot_password(body: ForgotPasswordSchema, db: AsyncSession, arq_pool: ArqRedis | None = None) -> None:
    await auth_service.request_password_reset(db, body.email, arq_pool=arq_pool)


async def reset_password(body: ResetPasswordSchema, db: AsyncSession) -> None:
    await auth_service.reset_password(db, body.token, body.new_password)
