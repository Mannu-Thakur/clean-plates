"""Settings service for Phase 8 administrative APIs."""

from __future__ import annotations

import re
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any

from arq.connections import ArqRedis
import asyncio
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.backup import BackupModel
from app.models.role import RoleModel
from app.models.user import RefreshTokenModel, UserModel
from app.schemas.auth import UserSchema
from app.schemas.common import (
    CacheResultSchema,
    LogoUrlSchema,
    OptimizeResultSchema,
    RestoreResultSchema,
    SystemInfoSchema,
    TempPasswordSchema,
)
from app.schemas.config import AppearanceConfigSchema, SecurityConfigSchema
from app.schemas.settings import BackupSchema, UserCreateSchema, UserUpdateSchema
from app.services import audit_service, backup_service, config_service, email_service

_ROLE_NAMES = {
    "super_admin",
    "institution_admin",
    "mess_admin",
    "analytics_viewer",
    "staff_operator",
}
_MAX_LOGO_BYTES = 5 * 1024 * 1024
_MAX_RESTORE_BYTES = 250 * 1024 * 1024
_LOGO_CONTENT_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
}
_LOGO_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}


def _utcnow() -> datetime:
    return datetime.utcnow()  # noqa: DTZ003


def _audit_user(current_user: UserSchema | None) -> dict[str, str]:
    if current_user is None:
        return {}
    return {"user_id": current_user.id, "user_name": current_user.name, "user_role": current_user.role}


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _logo_url_for_path(path: str) -> str:
    upload_root = Path(settings.UPLOAD_DIR).resolve()
    file_path = Path(path).resolve()
    try:
        rel = file_path.relative_to(upload_root).as_posix()
    except ValueError:
        rel = file_path.name
    return f"/static/uploads/{rel}"


async def _known_role(db: AsyncSession, role: str) -> bool:
    result = await db.execute(select(func.count(RoleModel.id)))
    role_rows = int(result.scalar_one() or 0)
    if role_rows == 0:
        return role in _ROLE_NAMES
    result = await db.execute(select(RoleModel).where(RoleModel.name == role))
    return result.scalar_one_or_none() is not None


async def _validate_role(db: AsyncSession, role: str) -> str:
    role = role.strip().lower()
    if not await _known_role(db, role):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown role '{role}'")
    return role


async def _validate_password(db: AsyncSession, password: str) -> None:
    security_config = await config_service.get_config(db, "security")
    min_length = int(security_config.get("min_password_length", 8))
    if len(password) < min_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {min_length} characters",
        )
    if security_config.get("require_uppercase", True) and not any(char.isupper() for char in password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must include an uppercase letter")
    if security_config.get("require_numbers", True) and not any(char.isdigit() for char in password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must include a number")


async def _generate_temp_password(db: AsyncSession) -> str:
    security_config = await config_service.get_config(db, "security")
    min_length = max(int(security_config.get("min_password_length", 8)), 12)
    while True:
        password = secrets.token_urlsafe(18)[: max(min_length, 12)]
        if not any(char.isupper() for char in password):
            password = f"A{password[1:]}"
        if not any(char.isdigit() for char in password):
            password = f"{password[:-1]}7"
        try:
            await _validate_password(db, password)
            return password
        except HTTPException:
            continue


async def _ensure_can_modify_user(db: AsyncSession, target: UserModel, current_user: UserSchema) -> None:
    if current_user.role == "super_admin":
        return
    if target.role == "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super admins can modify super admins")


async def _ensure_not_last_super_admin(db: AsyncSession, target: UserModel, new_role: str | None = None) -> None:
    if target.role != "super_admin":
        return
    if new_role == "super_admin":
        return
    result = await db.execute(
        select(func.count(UserModel.id)).where(UserModel.role == "super_admin", UserModel.is_active.is_(True))
    )
    if int(result.scalar_one() or 0) <= 1:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot remove the last active super admin")


async def list_users(db: AsyncSession) -> list[UserSchema]:
    result = await db.execute(select(UserModel).order_by(UserModel.created_at.desc()))
    return [UserSchema.model_validate(user) for user in result.scalars().all()]


async def create_user(
    db: AsyncSession,
    body: UserCreateSchema,
    *,
    current_user: UserSchema,
) -> UserSchema:
    role = await _validate_role(db, body.role)
    if role == "super_admin" and current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super admins can create super admins")

    email = _normalize_email(str(body.email))
    existing = (await db.execute(select(UserModel).where(UserModel.email == email))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists")

    password = body.password or await _generate_temp_password(db)
    await _validate_password(db, password)
    user = UserModel(
        email=email,
        password_hash=await hash_password(password),
        name=body.name.strip(),
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    await audit_service.log(
        db,
        event_type="settings.user_created",
        action="create",
        resource_type="user",
        resource_id=user.id,
        summary=f"Created user '{user.email}'",
        after_state=backup_service.user_state(user),
        **_audit_user(current_user),
    )

    await email_service.send_email(
        user.email,
        "Welcome to CleanPlates",
        (
            f"<p>Hello {user.name},</p>"
            "<p>Your CleanPlates account has been created.</p>"
            f"<p>Temporary password: <strong>{password}</strong></p>"
        ),
    )
    return UserSchema.model_validate(user)


async def update_user(
    db: AsyncSession,
    user_id: str,
    body: UserUpdateSchema,
    *,
    current_user: UserSchema,
) -> UserSchema:
    user = await db.get(UserModel, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await _ensure_can_modify_user(db, user, current_user)
    before = backup_service.user_state(user)

    data = body.model_dump(exclude_unset=True)
    new_role = data.get("role")
    if new_role is not None:
        new_role = await _validate_role(db, new_role)
        if new_role == "super_admin" and current_user.role != "super_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super admins can assign super admin")
        await _ensure_not_last_super_admin(db, user, new_role)
        user.role = new_role
    if data.get("email") is not None:
        email = _normalize_email(str(data["email"]))
        existing = (await db.execute(select(UserModel).where(UserModel.email == email, UserModel.id != user.id))).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists")
        user.email = email
    if data.get("name") is not None:
        user.name = str(data["name"]).strip()

    await db.flush()
    await audit_service.log(
        db,
        event_type="settings.user_updated",
        action="update",
        resource_type="user",
        resource_id=user.id,
        summary=f"Updated user '{user.email}'",
        before_state=before,
        after_state=backup_service.user_state(user),
        **_audit_user(current_user),
    )
    return UserSchema.model_validate(user)


async def deactivate_user(db: AsyncSession, user_id: str, *, current_user: UserSchema) -> None:
    user = await db.get(UserModel, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You cannot deactivate your own account")
    await _ensure_can_modify_user(db, user, current_user)
    await _ensure_not_last_super_admin(db, user, None)
    before = backup_service.user_state(user)
    user.is_active = False
    await db.execute(update(RefreshTokenModel).where(RefreshTokenModel.user_id == user.id).values(revoked=True))
    await db.flush()
    await audit_service.log(
        db,
        event_type="settings.user_deactivated",
        action="update",
        resource_type="user",
        resource_id=user.id,
        summary=f"Deactivated user '{user.email}'",
        before_state=before,
        after_state=backup_service.user_state(user),
        **_audit_user(current_user),
    )


async def reset_user_password(
    db: AsyncSession,
    user_id: str,
    *,
    current_user: UserSchema,
) -> TempPasswordSchema:
    user = await db.get(UserModel, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await _ensure_can_modify_user(db, user, current_user)

    password = await _generate_temp_password(db)
    user.password_hash = await hash_password(password)
    user.password_reset_token = None
    user.password_reset_expires_at = None
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.execute(update(RefreshTokenModel).where(RefreshTokenModel.user_id == user.id).values(revoked=True))
    await db.flush()
    await audit_service.log(
        db,
        event_type="settings.password_reset",
        action="update",
        resource_type="user",
        resource_id=user.id,
        summary=f"Reset password for '{user.email}'",
        **_audit_user(current_user),
    )
    await email_service.send_email(
        user.email,
        "CleanPlates temporary password",
        f"<p>Your CleanPlates password was reset.</p><p>Temporary password: <strong>{password}</strong></p>",
    )
    return TempPasswordSchema(temp_password=password, message="Temporary password generated and emailed")


async def get_security_config(db: AsyncSession) -> SecurityConfigSchema:
    return SecurityConfigSchema.model_validate(await config_service.get_config(db, "security"))


async def update_security_config(
    db: AsyncSession,
    body: SecurityConfigSchema,
    *,
    current_user: UserSchema,
) -> SecurityConfigSchema:
    data = await config_service.update_config(db, "security", body.model_dump(), current_user=current_user)
    return SecurityConfigSchema.model_validate(data)


async def list_backups(db: AsyncSession) -> list[BackupSchema]:
    result = await db.execute(select(BackupModel).order_by(BackupModel.created_at.desc()))
    return [BackupSchema.model_validate(backup) for backup in result.scalars().all()]


async def trigger_backup(
    db: AsyncSession,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
    backup_type: str = "manual",
) -> BackupSchema:
    filename = backup_service.new_backup_filename(backup_type)
    backup = BackupModel(
        filename=filename,
        file_path=str(Path(settings.BACKUPS_DIR) / filename),
        backup_type=backup_type,
        status="creating",
        triggered_by=current_user.id,
    )
    db.add(backup)
    await db.flush()
    await audit_service.log(
        db,
        event_type="backup.queued",
        action="create",
        resource_type="backup",
        resource_id=backup.id,
        summary=f"Queued {backup.backup_type} backup",
        after_state={"id": backup.id, "filename": backup.filename, "status": backup.status},
        **_audit_user(current_user),
    )
    await db.commit()
    if arq_pool is not None:
        await arq_pool.enqueue_job("create_backup_task", backup.id)
    else:
        backup = await backup_service.create_backup(db, backup.id)
        await db.commit()
    return BackupSchema.model_validate(backup)


async def get_backup_file(db: AsyncSession, backup_id: str) -> tuple[str, str]:
    backup = await db.get(BackupModel, backup_id)
    if backup is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found")
    if backup.status != "available":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Backup is not available")
    if not backup.file_path or not Path(backup.file_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup file is missing")
    return backup.file_path, Path(backup.file_path).name


async def _save_bounded_upload(upload: UploadFile, target_path: Path, max_bytes: int, allowed_suffixes: set[str]) -> int:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in allowed_suffixes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    try:
        with open(target_path, "wb") as handle:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Uploaded file is too large")
                await asyncio.to_thread(handle.write, chunk)
        return total
    except Exception:
        target_path.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()


async def restore_backup(
    db: AsyncSession,
    backup_file: UploadFile,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> RestoreResultSchema:
    suffix = Path(backup_file.filename or "").suffix.lower()
    if suffix != ".zip":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Backup restore file must be a .zip")
    restore_dir = Path(settings.BACKUPS_DIR) / "restore-uploads"
    restore_path = restore_dir / f"restore-{_utcnow().strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(4)}.zip"
    await _save_bounded_upload(backup_file, restore_path, _MAX_RESTORE_BYTES, {".zip"})
    await backup_service.validate_backup_zip(restore_path)

    await audit_service.log(
        db,
        event_type="backup.restore_queued",
        action="restore",
        resource_type="backup",
        resource_id=restore_path.name,
        summary="Queued database restore from uploaded backup",
        metadata={"filename": backup_file.filename},
        **_audit_user(current_user),
    )
    await db.commit()
    if arq_pool is not None:
        await arq_pool.enqueue_job("restore_backup_task", str(restore_path))
    else:
        await backup_service.stage_restore_from_zip(restore_path)
    return RestoreResultSchema(
        success=True,
        message="Restore staged. The application will restart to apply it.",
        restored_at=_utcnow(),
    )


async def get_appearance(db: AsyncSession) -> AppearanceConfigSchema:
    return AppearanceConfigSchema.model_validate(await config_service.get_config(db, "appearance"))


async def update_appearance(
    db: AsyncSession,
    body: AppearanceConfigSchema,
    *,
    current_user: UserSchema,
) -> AppearanceConfigSchema:
    data = await config_service.update_config(db, "appearance", body.model_dump(), current_user=current_user)
    return AppearanceConfigSchema.model_validate(data)


async def upload_logo(
    db: AsyncSession,
    image_file: UploadFile,
    *,
    current_user: UserSchema,
) -> LogoUrlSchema:
    suffix = Path(image_file.filename or "").suffix.lower()
    content_suffix = _LOGO_CONTENT_TYPES.get((image_file.content_type or "").lower())
    if suffix not in _LOGO_SUFFIXES and content_suffix is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logo must be an image file")
    suffix = content_suffix or suffix
    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "-", Path(image_file.filename or "logo").stem).strip("-") or "logo"
    filename = f"{safe_name}-{secrets.token_hex(8)}{suffix}"
    target = Path(settings.UPLOAD_DIR) / "logos" / filename
    await _save_bounded_upload(image_file, target, _MAX_LOGO_BYTES, _LOGO_SUFFIXES)
    logo_url = _logo_url_for_path(str(target))
    appearance = await config_service.get_config(db, "appearance")
    before = dict(appearance)
    appearance["logo_path"] = logo_url
    await config_service.update_config(db, "appearance", appearance, current_user=current_user)
    await audit_service.log(
        db,
        event_type="settings.logo_uploaded",
        action="update",
        resource_type="config",
        resource_id="appearance",
        summary="Uploaded institution logo",
        before_state=before,
        after_state=appearance,
        **_audit_user(current_user),
    )
    return LogoUrlSchema(logo_url=logo_url)


async def clear_cache(db: AsyncSession, *, current_user: UserSchema, redis: Any | None = None) -> CacheResultSchema:
    result = await backup_service.clear_cache(redis)
    await audit_service.log(
        db,
        event_type="maintenance.cache_cleared",
        action="delete",
        resource_type="cache",
        summary="Cleared Redis cache keys",
        after_state=result.model_dump(),
        **_audit_user(current_user),
    )
    return result


async def optimize_db(db: AsyncSession, *, current_user: UserSchema) -> OptimizeResultSchema:
    result = await backup_service.optimize_sqlite(db)
    await audit_service.log(
        db,
        event_type="maintenance.db_optimized",
        action="execute",
        resource_type="database",
        summary="Optimized SQLite database",
        after_state=result.model_dump(),
        **_audit_user(current_user),
    )
    return result


async def get_system_info() -> SystemInfoSchema:
    return await backup_service.collect_system_info()


async def export_all_data(db: AsyncSession, *, current_user: UserSchema) -> tuple[str, str]:
    export_dir = Path(settings.BACKUPS_DIR) / "exports"
    filename = f"cleanplates-export-{_utcnow().strftime('%Y%m%d-%H%M%S')}.zip"
    export_path = export_dir / filename
    file_size = await backup_service.export_all_data(db, export_path)
    await audit_service.log(
        db,
        event_type="maintenance.data_exported",
        action="export",
        resource_type="database",
        resource_id=filename,
        summary="Exported all application data",
        after_state={"filename": filename, "file_size": file_size},
        **_audit_user(current_user),
    )
    return str(export_path), filename
