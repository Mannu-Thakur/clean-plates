"""ARQ task functions for rule evaluation."""

from __future__ import annotations

from typing import Any

from app.services import rule_engine_service


async def evaluate_event(ctx: dict[str, Any], event_type: str, event_data: dict[str, Any]) -> None:
    """Evaluate one queued event against the latest active rules."""
    db_session_factory = ctx["db_session_factory"]
    arq_pool = ctx["redis"]
    async with db_session_factory() as db:
        try:
            await rule_engine_service.evaluate_event(
                event_type=event_type,
                event_data=event_data,
                db=db,
                arq_pool=arq_pool,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
