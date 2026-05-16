"""
Auth service — authentication, token management, password reset.

Ref: 02-controllers.md §1
"""

from __future__ import annotations

from datetime import datetime, timedelta

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
from app.services import audit_service


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
    """Validate credentials and return JWT pair + user profile.

    ⚠ F6-fix: Lockout settings should eventually read from
    config_service.get_config("security") instead of hardcoded settings.
    For Phase 1, we use the Settings defaults.
    """
    from app.core.config import settings

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
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = _utcnow() + timedelta(
                minutes=settings.LOCKOUT_DURATION_MINUTES
            )

        await db.flush()
        raise ValueError("Invalid email or password")

    # Successful login — reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = _utcnow()

    # Issue tokens
    access_token, expires_in = create_access_token(user.id, user.role)
    refresh_token, refresh_expires_at = create_refresh_token(user.id)

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
    access_token, expires_in = create_access_token(user.id, user.role)
    refresh_token, refresh_expires_at = create_refresh_token(user.id)

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


async def request_password_reset(db: AsyncSession, email: str) -> None:
    """Generate a password reset token and store its hash.

    NOTE: Email dispatch is stubbed until Phase 6 (EmailService).
    The reset token is still generated and stored; only email is deferred.
    """
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        # Don't reveal whether email exists — silently return
        return

    raw_token, hashed_token = generate_reset_token()
    user.password_reset_token = hashed_token
    user.password_reset_expires_at = _utcnow() + timedelta(hours=1)

    await db.flush()

    # TODO: Wire EmailService in Phase 6 — send raw_token to user.email
    # email_service.send_email(to=user.email, subject="Password Reset", ...)


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    """Verify reset token → hash new password → clear token."""
    if len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters")

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
