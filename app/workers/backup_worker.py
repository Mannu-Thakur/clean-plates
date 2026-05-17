"""ARQ tasks for backups, staged restores, and audit retention."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.config import settings
from app.models.backup import BackupModel
from app.services import audit_service, backup_service, config_service


def _utcnow() -> datetime:
    return datetime.utcnow()  # noqa: DTZ003


async def create_backup_task(ctx: dict[str, Any], backup_id: str) -> None:
    db_session_factory = ctx["db_session_factory"]
    async with db_session_factory() as db:
        try:
            await backup_service.create_backup(db, backup_id)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def auto_backup(ctx: dict[str, Any]) -> None:
    """Hourly cron entry that respects the dynamic backup_interval_hours config."""
    db_session_factory = ctx["db_session_factory"]
    async with db_session_factory() as db:
        try:
            system_config = await config_service.get_config(db, "system")
            interval_hours = int(system_config.get("backup_interval_hours", 24))
            result = await db.execute(
                select(BackupModel)
                .where(BackupModel.backup_type == "scheduled", BackupModel.status == "available")
                .order_by(BackupModel.created_at.desc())
                .limit(1)
            )
            last_backup = result.scalar_one_or_none()
            if last_backup and last_backup.created_at > _utcnow() - timedelta(hours=interval_hours):
                await db.commit()
                return
            backup = BackupModel(
                filename=backup_service.new_backup_filename("scheduled"),
                file_path="",
                backup_type="scheduled",
                status="creating",
                triggered_by=None,
            )
            backup.file_path = str(Path(settings.BACKUPS_DIR) / backup.filename)
            db.add(backup)
            await db.flush()
            await backup_service.create_backup(db, backup.id)
            await audit_service.log(
                db,
                event_type="backup.created",
                action="create",
                resource_type="backup",
                resource_id=backup.id,
                summary="Created scheduled backup",
                after_state={"filename": backup.filename, "status": backup.status, "file_size": backup.file_size},
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def purge_old_audit_events(ctx: dict[str, Any]) -> None:
    db_session_factory = ctx["db_session_factory"]
    async with db_session_factory() as db:
        try:
            system_config = await config_service.get_config(db, "system")
            retention_days = int(system_config.get("audit_retention_days", 90))
            deleted = await audit_service.purge_old_events(db, retention_days)
            if deleted:
                await audit_service.log(
                    db,
                    event_type="audit.purged",
                    action="delete",
                    resource_type="audit",
                    summary=f"Purged {deleted} old audit events",
                    metadata={"deleted": deleted, "retention_days": retention_days},
                )
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def restore_backup_task(ctx: dict[str, Any], backup_zip_path: str) -> None:  # noqa: ARG001
    await backup_service.stage_restore_from_zip(backup_zip_path)
