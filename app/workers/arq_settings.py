"""ARQ worker settings for CleanPlates background jobs."""

from __future__ import annotations

import logging
from typing import Any

from arq.connections import RedisSettings

from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.workers.rule_worker import evaluate_event


logger = logging.getLogger("cleanplates.worker")


async def on_startup(ctx: dict[str, Any]) -> None:
    """Attach worker-local dependencies to ARQ context."""
    ctx["db_session_factory"] = AsyncSessionLocal

    # Phase 6/8 models do not exist yet. Keep the recovery hook future-proof so
    # adding those models later does not require changing the worker contract.
    async with AsyncSessionLocal() as db:
        try:
            from app.models.report import BackupModel, ReportModel  # type: ignore

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
    await engine.dispose()


class WorkerSettings:
    functions = [evaluate_event]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = on_startup
    on_shutdown = on_shutdown
    # P6-fix: SQLite lock resilience — retry failed jobs up to 3 times
    # with a 1-second delay before marking as permanently failed.
    max_tries = 3
    retry_failed_delay = 1
