"""ARQ task functions for Phase 5 aggregation jobs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.services import aggregation_service
from app.services import ws_service


async def run_hourly_aggregation(ctx: dict[str, Any]) -> None:
    db_session_factory = ctx["db_session_factory"]
    arq_pool = ctx["redis"]
    async with db_session_factory() as db:
        try:
            writes = await aggregation_service.run_hourly_aggregation(db)
            await db.commit()
            if writes:
                await ws_service.broadcast_to_room(
                    "dashboard",
                    {
                        "type": "kpi_update",
                        "period": "hourly",
                        "writes": writes,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                    redis=arq_pool,
                )
        except Exception:
            await db.rollback()
            raise


async def run_daily_aggregation(ctx: dict[str, Any]) -> None:
    db_session_factory = ctx["db_session_factory"]
    async with db_session_factory() as db:
        try:
            await aggregation_service.run_daily_aggregation(db)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def compute_sustainability_scores(ctx: dict[str, Any]) -> None:
    db_session_factory = ctx["db_session_factory"]
    async with db_session_factory() as db:
        try:
            await aggregation_service.compute_sustainability_scores(db)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def check_device_offline_status(ctx: dict[str, Any]) -> None:
    db_session_factory = ctx["db_session_factory"]
    arq_pool = ctx["redis"]
    async with db_session_factory() as db:
        try:
            await aggregation_service.check_device_offline_status(db, arq_pool=arq_pool)
            await db.commit()
        except Exception:
            await db.rollback()
            raise
