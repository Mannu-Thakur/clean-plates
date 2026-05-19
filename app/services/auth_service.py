"""
Auth service — authentication, token management, password reset.

Ref: 02-controllers.md §1
"""

from __future__ import annotations

from datetime import datetime, timedelta

from arq.connections import ArqRedis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_reset_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import RefreshTokenModel, UserModel
from app.schemas.auth import LoginResponseSchema, TokenPairSchema, UserSchema
from app.services import audit_service, config_service


def _utcnow() -> datetime:
    """Naive UTC - safe for SQLite datetime columns."""
    return datetime.utcnow()  # noqa: DTZ003


async def authenticate(
    db: AsyncSession,
    email: str,
    password: str,
    remember_me: bool = False,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> LoginResponseSchema:
    """Validate credentials and return JWT pair + user profile."""
    security_config = await config_service.get_config(db, "security")
    max_attempts = int(security_config.get("max_login_attempts", 5))
    lockout_minutes = int(security_config.get("lockout_duration_minutes", 15))
    access_minutes = int(security_config.get("access_token_expiry_minutes", 1440))
    refresh_days = int(security_config.get("refresh_token_expiry_days", 30))

    result = await db.execute(select(UserModel).where(UserModel.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise PermissionError("Account is deactivated")

    # Check lockout
    if user.locked_until and user.locked_until > _utcnow():
        remaining = int((user.locked_until - _utcnow()).total_seconds() // 60) + 1
        raise PermissionError(f"Account is locked. Try again in {remaining} minutes.")

    # Verify password
    if not await verify_password(password, user.password_hash):
        user.failed_login_attempts += 1

        # Lock account if max attempts exceeded
        if user.failed_login_attempts >= max_attempts:
            user.locked_until = _utcnow() + timedelta(minutes=lockout_minutes)

        await db.flush()
        raise ValueError("Invalid email or password")

    # Successful login — reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = _utcnow()

    # Issue tokens
    access_token, expires_in = create_access_token(user.id, user.role, expires_minutes=access_minutes)
    refresh_token, refresh_expires_at = create_refresh_token(user.id, expires_days=refresh_days)

    # Store refresh token hash
    db.add(RefreshTokenModel(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=refresh_expires_at,
    ))

    await db.flush()

    # Audit
    await audit_service.log(
        db,
        event_type="auth.login",
        action="login",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        user_name=user.name,
        user_role=user.role,
        ip_address=ip_address,
        user_agent=user_agent,
        summary=f"User '{user.email}' logged in",
    )

    return LoginResponseSchema(
        tokens=TokenPairSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        ),
        user=UserSchema.model_validate(user),
    )


async def issue_tokens(user: UserModel, db: AsyncSession) -> TokenPairSchema:
    """Issue a fresh access + refresh token pair for a user."""
    security_config = await config_service.get_config(db, "security")
    access_token, expires_in = create_access_token(
        user.id,
        user.role,
        expires_minutes=int(security_config.get("access_token_expiry_minutes", 1440)),
    )
    refresh_token, refresh_expires_at = create_refresh_token(
        user.id,
        expires_days=int(security_config.get("refresh_token_expiry_days", 30)),
    )

    db.add(RefreshTokenModel(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=refresh_expires_at,
    ))
    await db.flush()

    return TokenPairSchema(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


async def refresh_tokens(db: AsyncSession, refresh_token_str: str) -> TokenPairSchema:
    """Verify refresh token → issue new access token → rotate refresh token."""
    payload = decode_token(refresh_token_str)
    if payload is None or payload.get("type") != "refresh":
        raise ValueError("Invalid refresh token")

    token_hash = hash_token(refresh_token_str)
    result = await db.execute(
        select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()

    if stored is None or stored.revoked:
        raise ValueError("Refresh token not found or already revoked")

    if stored.expires_at < _utcnow():
        raise ValueError("Refresh token has expired")

    # Revoke old token
    stored.revoked = True

    # Fetch user
    user_result = await db.execute(select(UserModel).where(UserModel.id == stored.user_id))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise ValueError("User not found or inactive")

    # Issue new pair
    return await issue_tokens(user, db)


async def revoke_token(db: AsyncSession, refresh_token_str: str, user_id: str) -> None:
    """Revoke a specific refresh token (logout)."""
    token_hash = hash_token(refresh_token_str)
    await db.execute(
        update(RefreshTokenModel)
        .where(
            RefreshTokenModel.token_hash == token_hash,
            RefreshTokenModel.user_id == user_id,
        )
        .values(revoked=True)
    )

    await audit_service.log(
        db,
        event_type="auth.logout",
        action="logout",
        resource_type="user",
        resource_id=user_id,
        user_id=user_id,
        summary="User logged out",
    )


async def request_password_reset(db: AsyncSession, email: str, *, arq_pool: ArqRedis | None = None) -> None:
    """Generate a password reset token, store its hash, and dispatch reset email."""
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        # Don't reveal whether email exists — silently return
        return

    raw_token, hashed_token = generate_reset_token()
    user.password_reset_token = hashed_token
    user.password_reset_expires_at = _utcnow() + timedelta(hours=1)

    await db.flush()

    subject = "CleanPlates password reset"
    body_html = (
        "<p>A password reset was requested for your CleanPlates account.</p>"
        f"<p>Use this reset token within 1 hour:</p><p><strong>{raw_token}</strong></p>"
        "<p>If you did not request this, you can ignore this email.</p>"
    )
    if arq_pool is not None:
        await db.commit()
        await arq_pool.enqueue_job("send_email_task", user.email, subject, body_html)
    else:
        from app.services import email_service

        await email_service.send_email(user.email, subject, body_html)


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    """Verify reset token → hash new password → clear token."""
    security_config = await config_service.get_config(db, "security")
    min_length = int(security_config.get("min_password_length", 8))
    if len(new_password) < min_length:
        raise ValueError(f"Password must be at least {min_length} characters")
    if security_config.get("require_uppercase", True) and not any(char.isupper() for char in new_password):
        raise ValueError("Password must include an uppercase letter")
    if security_config.get("require_numbers", True) and not any(char.isdigit() for char in new_password):
        raise ValueError("Password must include a number")

    hashed_token = hash_token(token)
    result = await db.execute(
        select(UserModel).where(UserModel.password_reset_token == hashed_token)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise ValueError("Invalid reset token")

    if user.password_reset_expires_at and user.password_reset_expires_at < _utcnow():
        raise ValueError("Reset token has expired")

    user.password_hash = await hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires_at = None
    user.failed_login_attempts = 0
    user.locked_until = None

    await db.flush()

    await audit_service.log(
        db,
        event_type="auth.password_reset",
        action="update",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        user_name=user.name,
        summary=f"Password reset for '{user.email}'",
    )
