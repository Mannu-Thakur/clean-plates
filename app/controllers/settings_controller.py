"""Settings controller - thin dispatch layer."""

from __future__ import annotations

from arq.connections import ArqRedis
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.services import settings_service


async def list_users(db: AsyncSession) -> list[UserSchema]:
    return await settings_service.list_users(db)


async def create_user(db: AsyncSession, body: UserCreateSchema, *, current_user: UserSchema) -> UserSchema:
    return await settings_service.create_user(db, body, current_user=current_user)


async def update_user(
    db: AsyncSession,
    user_id: str,
    body: UserUpdateSchema,
    *,
    current_user: UserSchema,
) -> UserSchema:
    return await settings_service.update_user(db, user_id, body, current_user=current_user)


async def deactivate_user(db: AsyncSession, user_id: str, *, current_user: UserSchema) -> None:
    await settings_service.deactivate_user(db, user_id, current_user=current_user)


async def reset_user_password(
    db: AsyncSession,
    user_id: str,
    *,
    current_user: UserSchema,
) -> TempPasswordSchema:
    return await settings_service.reset_user_password(db, user_id, current_user=current_user)


async def get_security_config(db: AsyncSession) -> SecurityConfigSchema:
    return await settings_service.get_security_config(db)


async def update_security_config(
    db: AsyncSession,
    body: SecurityConfigSchema,
    *,
    current_user: UserSchema,
) -> SecurityConfigSchema:
    return await settings_service.update_security_config(db, body, current_user=current_user)


async def list_backups(db: AsyncSession) -> list[BackupSchema]:
    return await settings_service.list_backups(db)


async def trigger_backup(
    db: AsyncSession,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> BackupSchema:
    return await settings_service.trigger_backup(db, current_user=current_user, arq_pool=arq_pool)


async def download_backup(db: AsyncSession, backup_id: str) -> tuple[str, str]:
    return await settings_service.get_backup_file(db, backup_id)


async def restore_backup(
    db: AsyncSession,
    backup_file: UploadFile,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> RestoreResultSchema:
    return await settings_service.restore_backup(db, backup_file, current_user=current_user, arq_pool=arq_pool)


async def get_appearance(db: AsyncSession) -> AppearanceConfigSchema:
    return await settings_service.get_appearance(db)


async def update_appearance(
    db: AsyncSession,
    body: AppearanceConfigSchema,
    *,
    current_user: UserSchema,
) -> AppearanceConfigSchema:
    return await settings_service.update_appearance(db, body, current_user=current_user)


async def upload_logo(db: AsyncSession, image_file: UploadFile, *, current_user: UserSchema) -> LogoUrlSchema:
    return await settings_service.upload_logo(db, image_file, current_user=current_user)


async def clear_cache(
    db: AsyncSession,
    *,
    current_user: UserSchema,
    redis=None,
) -> CacheResultSchema:
    return await settings_service.clear_cache(db, current_user=current_user, redis=redis)


async def optimize_db(db: AsyncSession, *, current_user: UserSchema) -> OptimizeResultSchema:
    return await settings_service.optimize_db(db, current_user=current_user)


async def get_system_info() -> SystemInfoSchema:
    return await settings_service.get_system_info()


async def export_all_data(db: AsyncSession, *, current_user: UserSchema) -> tuple[str, str]:
    return await settings_service.export_all_data(db, current_user=current_user)
