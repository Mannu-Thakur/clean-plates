"""Settings routes for Phase 8 administration APIs."""

from __future__ import annotations

from uuid import UUID

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import settings_controller
from app.core.redis import get_arq_pool
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.auth import UserSchema
from app.schemas.common import (
    CacheResultSchema,
    LogoUrlSchema,
    MessageSchema,
    OptimizeResultSchema,
    RestoreResultSchema,
    SystemInfoSchema,
    TempPasswordSchema,
)
from app.schemas.config import AppearanceConfigSchema, SecurityConfigSchema
from app.schemas.settings import BackupSchema, UserCreateSchema, UserUpdateSchema

router = APIRouter(prefix="/settings", tags=["Settings"])

SETTINGS_READ_ROLES = ("super_admin", "institution_admin")
SETTINGS_WRITE_ROLES = ("super_admin",)
SETTINGS_APPEARANCE_ROLES = ("super_admin", "institution_admin")


@router.get("/users", response_model=list[UserSchema])
async def list_users(
    current_user: UserSchema = Depends(require_roles(*SETTINGS_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await settings_controller.list_users(db)


@router.post("/users", response_model=UserSchema, status_code=201)
async def create_user(
    body: UserCreateSchema,
    current_user: UserSchema = Depends(require_roles(*SETTINGS_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await settings_controller.create_user(db, body, current_user=current_user)


@router.patch("/users/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: UUID,
    body: UserUpdateSchema,
    current_user: UserSchema = Depends(require_roles(*SETTINGS_READ_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await settings_controller.update_user(db, str(user_id), body, current_user=current_user)


@router.post("/users/{user_id}/deactivate", response_model=MessageSchema)
async def deactivate_user(
    user_id: UUID,
    current_user: UserSchema = Depends(require_roles(*SETTINGS_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    await settings_controller.deactivate_user(db, str(user_id), current_user=current_user)
    return MessageSchema(message="User deactivated")


@router.post("/users/{user_id}/reset-password", response_model=TempPasswordSchema)
async def reset_user_password(
    user_id: UUID,
    current_user: UserSchema = Depends(require_roles(*SETTINGS_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await settings_controller.reset_user_password(db, str(user_id), current_user=current_user)


@router.get("/security", response_model=SecurityConfigSchema)
async def get_security_config(
    current_user: UserSchema = Depends(require_roles(*SETTINGS_WRITE_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await settings_controller.get_security_config(db)


@router.patch("/security", response_model=SecurityConfigSchema)
async def update_security_config(
    body: SecurityConfigSchema,
    current_user: UserSchema = Depends(require_roles(*SETTINGS_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await settings_controller.update_security_config(db, body, current_user=current_user)


@router.get("/backups", response_model=list[BackupSchema])
async def list_backups(
    current_user: UserSchema = Depends(require_roles(*SETTINGS_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await settings_controller.list_backups(db)


@router.post("/backups", response_model=BackupSchema, status_code=201)
async def trigger_backup(
    current_user: UserSchema = Depends(require_roles(*SETTINGS_READ_ROLES)),
    db: AsyncSession = Depends(get_db_session),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
):
    return await settings_controller.trigger_backup(db, current_user=current_user, arq_pool=arq_pool)


@router.post("/backups/restore", response_model=RestoreResultSchema)
async def restore_backup(
    backup_file: UploadFile = File(...),
    current_user: UserSchema = Depends(require_roles(*SETTINGS_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
):
    return await settings_controller.restore_backup(
        db,
        backup_file,
        current_user=current_user,
        arq_pool=arq_pool,
    )


@router.get("/backups/{backup_id}/download")
async def download_backup(
    backup_id: UUID,
    current_user: UserSchema = Depends(require_roles(*SETTINGS_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    file_path, filename = await settings_controller.download_backup(db, str(backup_id))
    return FileResponse(file_path, filename=filename)


@router.get("/appearance", response_model=AppearanceConfigSchema)
async def get_appearance(
    current_user: UserSchema = Depends(require_roles(*SETTINGS_APPEARANCE_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await settings_controller.get_appearance(db)


@router.patch("/appearance", response_model=AppearanceConfigSchema)
async def update_appearance(
    body: AppearanceConfigSchema,
    current_user: UserSchema = Depends(require_roles(*SETTINGS_APPEARANCE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await settings_controller.update_appearance(db, body, current_user=current_user)


@router.post("/appearance/logo", response_model=LogoUrlSchema)
async def upload_logo(
    image_file: UploadFile = File(...),
    current_user: UserSchema = Depends(require_roles(*SETTINGS_APPEARANCE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await settings_controller.upload_logo(db, image_file, current_user=current_user)


@router.post("/maintenance/clear-cache", response_model=CacheResultSchema)
async def clear_cache(
    current_user: UserSchema = Depends(require_roles(*SETTINGS_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
):
    return await settings_controller.clear_cache(db, current_user=current_user, redis=arq_pool)


@router.post("/maintenance/optimize-db", response_model=OptimizeResultSchema)
async def optimize_db(
    current_user: UserSchema = Depends(require_roles(*SETTINGS_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await settings_controller.optimize_db(db, current_user=current_user)


@router.get("/maintenance/system-info", response_model=SystemInfoSchema)
async def get_system_info(
    current_user: UserSchema = Depends(require_roles(*SETTINGS_READ_ROLES)),  # noqa: ARG001
):
    return await settings_controller.get_system_info()


@router.get("/maintenance/export-all")
async def export_all_data(
    current_user: UserSchema = Depends(require_roles(*SETTINGS_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    file_path, filename = await settings_controller.export_all_data(db, current_user=current_user)
    return FileResponse(file_path, filename=filename)
