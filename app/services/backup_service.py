"""SQLite backup, export, and staged restore helpers."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import platform
import shutil
import sys
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.generators.csv_generator import write_csv
from app.models.audit import AuditEventModel
from app.models.backup import BackupModel
from app.models.config import ConfigModel
from app.models.user import UserModel
from app.schemas.auth import UserSchema
from app.schemas.common import CacheResultSchema, OptimizeResultSchema, SystemInfoSchema

logger = logging.getLogger("cleanplates.backup")

_START_MONOTONIC = time.monotonic()
_MAX_RESTORE_ZIP_BYTES = 250 * 1024 * 1024


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _audit_user(current_user: UserSchema | None) -> dict[str, str]:
    if current_user is None:
        return {}
    return {"user_id": current_user.id, "user_name": current_user.name, "user_role": current_user.role}


def _backups_dir() -> Path:
    path = Path(settings.BACKUPS_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _data_dir() -> Path:
    db_path = sqlite_db_path()
    if db_path is not None and db_path != Path(":memory:"):
        return db_path.parent
    path = Path("./data")
    path.mkdir(parents=True, exist_ok=True)
    return path


def sqlite_db_path() -> Path | None:
    """Return the configured SQLite database path, if this deployment uses one."""
    prefix = "sqlite+aiosqlite:///"
    if not settings.DATABASE_URL.startswith(prefix):
        return None
    raw = settings.DATABASE_URL.removeprefix(prefix)
    if raw == ":memory:":
        return Path(":memory:")
    return Path(raw)


def restart_lock_path() -> Path:
    return _data_dir() / "restart.lock"


def staging_restore_path() -> Path:
    return _data_dir() / "staging_restore.db"


def _quote_sqlite_path(path: Path) -> str:
    return str(path).replace("'", "''")


async def _vacuum_into(db: AsyncSession, output_path: Path) -> None:
    """Create a SQLite-safe snapshot using VACUUM INTO.

    A direct file copy is intentionally avoided because WAL mode can keep
    committed pages in the ``-wal`` file. Opening a fresh sqlite connection and
    issuing VACUUM INTO produces a self-contained database file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.unlink(missing_ok=True)
    db_path = sqlite_db_path()

    if db_path is not None and db_path != Path(":memory:") and db_path.exists():
        try:
            import aiosqlite

            async with aiosqlite.connect(str(db_path)) as conn:
                await conn.execute("PRAGMA foreign_keys=ON")
                try:
                    await conn.execute("VACUUM INTO ?", (str(output_path),))
                except Exception:
                    await conn.execute(f"VACUUM INTO '{_quote_sqlite_path(output_path)}'")
                await conn.commit()
            return
        except Exception:
            logger.exception("VACUUM INTO failed against configured database path")
            output_path.unlink(missing_ok=True)
            raise

    await db.commit()
    await db.execute(text(f"VACUUM INTO '{_quote_sqlite_path(output_path)}'"))
    await db.commit()


async def create_backup(db: AsyncSession, backup_id: str) -> BackupModel:
    """Create a ZIP backup for an existing BackupModel row."""
    backup = await db.get(BackupModel, backup_id)
    if backup is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found")
    if backup.status == "available" and backup.file_path and Path(backup.file_path).exists():
        return backup

    backup.status = "creating"
    backup.file_size = None
    await db.flush()

    work_dir = _backups_dir() / "tmp"
    work_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = work_dir / f"{backup.id}.db"
    zip_path = _backups_dir() / backup.filename

    try:
        await _vacuum_into(db, snapshot_path)
        zip_path.unlink(missing_ok=True)
        
        def _zip_backup() -> None:
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.write(snapshot_path, arcname="cleanplates.db")
                manifest = {
                    "backup_id": backup.id,
                    "created_at": _utcnow().isoformat(),
                    "backup_type": backup.backup_type,
                    "app_version": settings.APP_VERSION,
                }
                archive.writestr("manifest.json", json.dumps(manifest, indent=2))
                
        await asyncio.to_thread(_zip_backup)
        backup.file_path = str(zip_path)
        backup.file_size = zip_path.stat().st_size
        backup.status = "available"
        await db.flush()
        return backup
    except Exception as exc:
        backup.status = "failed"
        await db.flush()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Backup failed: {exc}") from exc
    finally:
        snapshot_path.unlink(missing_ok=True)


async def validate_backup_zip(path: Path) -> None:
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found")
    if path.suffix.lower() != ".zip":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Backup must be a .zip file")
    if path.stat().st_size > _MAX_RESTORE_ZIP_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Backup file is too large")
    is_valid = await asyncio.to_thread(zipfile.is_zipfile, path)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid backup zip")


async def stage_restore_from_zip(path: str | Path) -> Path:
    """Extract a backup DB to staging and create restart.lock.

    The active database is never overwritten here. ``entrypoint.sh`` performs
    the swap before the next process boot, after removing old WAL/SHM files.
    """
    zip_path = Path(path)
    await validate_backup_zip(zip_path)
    staging = staging_restore_path()
    staging.parent.mkdir(parents=True, exist_ok=True)
    staging.unlink(missing_ok=True)

    def _extract_staging() -> None:
        with zipfile.ZipFile(zip_path) as archive:
            candidates = [
                info
                for info in archive.infolist()
                if not info.is_dir() and Path(info.filename).name.lower().endswith(".db")
            ]
            if not candidates:
                raise ValueError("Backup zip does not contain a database")
            db_member = sorted(candidates, key=lambda item: (Path(item.filename).name != "cleanplates.db", item.filename))[0]
            if db_member.file_size > _MAX_RESTORE_ZIP_BYTES:
                raise ValueError("Database backup is too large")
            with archive.open(db_member) as source, open(staging, "wb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)

    try:
        await asyncio.to_thread(_extract_staging)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    restart_lock_path().write_text("restore staged\n", encoding="utf-8")
    return staging


async def watch_restart_lock(poll_seconds: float = 2.0) -> None:
    """Exit the process when a staged restore requests a coordinated restart."""
    lock_path = restart_lock_path()
    while True:
        if lock_path.exists():
            logger.warning("Detected %s; exiting for staged database restore", lock_path)
            os._exit(0)  # noqa: S404,PLR1722 - intentional container restart signal
        await asyncio.sleep(poll_seconds)


async def export_all_data(db: AsyncSession, export_path: Path) -> int:
    """Package a DB snapshot, config dump, audit CSV, and uploads into a ZIP."""
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.unlink(missing_ok=True)
    snapshot_path = export_path.with_suffix(".db")
    audit_csv_path = export_path.with_suffix(".audit.csv")
    try:
        await _vacuum_into(db, snapshot_path)

        config_rows = (await db.execute(select(ConfigModel))).scalars().all()
        config_dump = [
            {"section": row.section, "key": row.key, "value": row.value, "updated_at": row.updated_at.isoformat()}
            for row in config_rows
        ]

        audit_rows = (await db.execute(select(AuditEventModel).order_by(AuditEventModel.created_at.desc()).limit(5000))).scalars().all()
        await write_csv(
            str(audit_csv_path),
            ["created_at", "event_type", "action", "resource_type", "resource_id", "user_name", "summary"],
            [
                {
                    "created_at": row.created_at.isoformat(sep=" ", timespec="seconds"),
                    "event_type": row.event_type,
                    "action": row.action,
                    "resource_type": row.resource_type,
                    "resource_id": row.resource_id or "",
                    "user_name": row.user_name or "System",
                    "summary": row.summary,
                }
                for row in audit_rows
            ],
        )

        def _zip_export() -> None:
            with zipfile.ZipFile(export_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.write(snapshot_path, arcname="database/cleanplates.db")
                archive.writestr("config/system_config.json", json.dumps(config_dump, indent=2, default=str))
                archive.write(audit_csv_path, arcname="audit/audit_log.csv")
                uploads_dir = Path(settings.UPLOAD_DIR)
                if uploads_dir.exists():
                    for file_path in uploads_dir.rglob("*"):
                        if file_path.is_file():
                            archive.write(file_path, arcname=f"uploads/{file_path.relative_to(uploads_dir).as_posix()}")
        
        await asyncio.to_thread(_zip_export)
        return export_path.stat().st_size
    finally:
        snapshot_path.unlink(missing_ok=True)
        audit_csv_path.unlink(missing_ok=True)


async def optimize_sqlite(db: AsyncSession) -> OptimizeResultSchema:
    """Run VACUUM and ANALYZE and report reclaimed disk space."""
    db_path = sqlite_db_path()
    before = db_path.stat().st_size if db_path is not None and db_path.exists() else 0
    if db_path is not None and db_path != Path(":memory:") and db_path.exists():
        import aiosqlite

        async with aiosqlite.connect(str(db_path)) as conn:
            await conn.execute("VACUUM")
            await conn.execute("ANALYZE")
            await conn.commit()
    else:
        await db.commit()
        try:
            await db.execute(text("VACUUM"))
            await db.execute(text("ANALYZE"))
            await db.commit()
        except Exception:
            await db.rollback()
            raise
    after = db_path.stat().st_size if db_path is not None and db_path.exists() else before
    freed_mb = max(before - after, 0) / (1024 * 1024)
    return OptimizeResultSchema(success=True, freed_mb=round(freed_mb, 3))


async def collect_system_info() -> SystemInfoSchema:
    db_path = sqlite_db_path()
    db_size = db_path.stat().st_size if db_path is not None and db_path.exists() else 0
    disk = shutil.disk_usage(Path.cwd())
    cpu_pct = 0.0
    if hasattr(os, "getloadavg"):
        try:
            load_1m = os.getloadavg()[0]
            cpu_count = os.cpu_count() or 1
            cpu_pct = min(round((load_1m / cpu_count) * 100, 2), 100.0)
        except OSError:
            cpu_pct = 0.0

    return SystemInfoSchema(
        os_version=f"{platform.system()} {platform.release()}".strip(),
        python_version=sys.version.split()[0],
        app_version=settings.APP_VERSION,
        db_size_mb=round(db_size / (1024 * 1024), 3),
        uptime_seconds=round(time.monotonic() - _START_MONOTONIC, 3),
        disk_usage_pct=round((disk.used / disk.total) * 100, 2) if disk.total else 0.0,
        ram_usage_pct=0.0,
        cpu_usage_pct=cpu_pct,
    )


async def clear_cache(redis: Any | None) -> CacheResultSchema:
    """Delete known cache/rate-limit keys without flushing ARQ queues."""
    if redis is None:
        return CacheResultSchema(cleared=False, keys_removed=0)
    patterns = ("cleanplates:cache:*", "cache:*", "rl:*")
    removed = 0
    for pattern in patterns:
        try:
            keys = []
            async for key in redis.scan_iter(match=pattern, count=500):
                keys.append(key)
                if len(keys) >= 500:
                    removed += int(await redis.delete(*keys))
                    keys.clear()
            if keys:
                removed += int(await redis.delete(*keys))
        except AttributeError:
            if hasattr(redis, "flushdb"):
                before = int(await redis.dbsize()) if hasattr(redis, "dbsize") else 0
                await redis.flushdb()
                removed = before
                break
    return CacheResultSchema(cleared=True, keys_removed=removed)


def new_backup_filename(backup_type: str) -> str:
    stamp = _utcnow().strftime("%Y%m%d-%H%M%S")
    return f"cleanplates-{backup_type}-{stamp}.zip"


def user_state(user: UserModel) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "is_active": user.is_active,
    }
