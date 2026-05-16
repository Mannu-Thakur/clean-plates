"""Reliable rule-event dispatch helpers."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from arq.connections import ArqRedis

from app.core.config import settings
from app.engine.event_bus import EventBus


event_bus = EventBus(settings.REDIS_URL)
logger = logging.getLogger("cleanplates.rule_events")


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [_jsonable(item) for item in value]
    return value


async def dispatch_rule_event(
    arq_pool: ArqRedis | None,
    event_type: str,
    event_data: dict[str, Any],
    *,
    depth: int = 1,
) -> None:
    """Enqueue a rule-evaluation job and publish the same event for UI fan-out.

    If Redis is unavailable, callers still commit their primary DB work. The
    application already stores entries/warnings/penalties as source-of-truth;
    background evaluation is best effort until the pool exists.
    """
    if arq_pool is None:
        return

    payload = {
        "event_type": event_type,
        "depth": depth,
        "timestamp": datetime.now(UTC).isoformat(),
        **_jsonable(event_data),
    }
    try:
        await arq_pool.enqueue_job("evaluate_event", event_type, payload)
        await event_bus.publish(event_type, payload, redis=arq_pool)
    except Exception:
        logger.exception("Failed to dispatch rule event %s", event_type)
