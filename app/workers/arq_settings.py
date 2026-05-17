"""ARQ worker settings for CleanPlates background jobs."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from typing import Any

from arq import cron
from arq.connections import RedisSettings

from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.workers.aggregation_worker import (
    check_device_offline_status,
    compute_sustainability_scores,
    run_daily_aggregation,
    run_hourly_aggregation,
)
from app.services import backup_service
from app.workers.backup_worker import (
    auto_backup,
    create_backup_task,
    purge_old_audit_events,
    restore_backup_task,
)
from app.workers.rule_worker import evaluate_event
from app.workers.report_worker import (
    execute_scheduled_reports,
    generate_report_task,
    send_email_task,
    send_notification_task,
    send_scheduled_notifications,
)


logger = logging.getLogger("cleanplates.worker")


async def on_startup(ctx: dict[str, Any]) -> None:
    """Attach worker-local dependencies to ARQ context."""
    ctx["db_session_factory"] = AsyncSessionLocal
    ctx["restart_lock_task"] = asyncio.create_task(backup_service.watch_restart_lock())

    # Recover records left in in-progress states if the worker restarted mid-job.
    async with AsyncSessionLocal() as db:
        try:
            from app.models.backup import BackupModel
            from app.models.report import ReportModel

            for model, stuck_status in ((ReportModel, "generating"), (BackupModel, "creating")):
                result = await db.execute(
                    model.__table__.update().where(model.status == stuck_status).values(status="failed")
                )
                if result.rowcount:
                    logger.warning("Recovered %s stuck %s rows", result.rowcount, model.__tablename__)
            await db.commit()
        except ModuleNotFoundError:
            await db.rollback()
        except Exception:
            await db.rollback()
            logger.exception("Could not run stuck job recovery")


async def on_shutdown(ctx: dict[str, Any]) -> None:  # noqa: ARG001
    restart_task = ctx.get("restart_lock_task")
    if restart_task is not None:
        restart_task.cancel()
        with suppress(asyncio.CancelledError):
            await restart_task
    await engine.dispose()


class WorkerSettings:
    functions = [
        evaluate_event,
        run_hourly_aggregation,
        run_daily_aggregation,
        compute_sustainability_scores,
        check_device_offline_status,
        generate_report_task,
        execute_scheduled_reports,
        send_scheduled_notifications,
        send_notification_task,
        send_email_task,
        create_backup_task,
        auto_backup,
        purge_old_audit_events,
        restore_backup_task,
    ]
    cron_jobs = [
        cron(run_hourly_aggregation, minute={0, 30}),
        cron(run_daily_aggregation, minute={0, 30}),
        cron(compute_sustainability_scores, minute={0, 15, 30, 45}),
        cron(check_device_offline_status, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),
        cron(execute_scheduled_reports, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),
        cron(send_scheduled_notifications, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),
        cron(auto_backup, minute=0),
        cron(purge_old_audit_events, hour=3, minute=0),
    ]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = on_startup
    on_shutdown = on_shutdown
    # P6-fix: SQLite lock resilience — retry failed jobs up to 3 times
    # with a 1-second delay before marking as permanently failed.
    max_tries = 3
    retry_failed_delay = 1
