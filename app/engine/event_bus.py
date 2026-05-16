"""
Redis Pub/Sub event bus for real-time fan-out.

Rule evaluation itself uses ARQ jobs. This bus is a best-effort side channel
for Phase 7 WebSocket fan-out and device commands.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from redis.asyncio import Redis


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


class EventBus:
    """Minimal Redis Pub/Sub event bus."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis: Redis | None = None
        self._handlers: dict[str, list[Callable[[dict[str, Any]], Awaitable[None]]]] = {}

    async def _client(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    def channel(self, event_type: str) -> str:
        return f"cleanplates:events:{event_type}"

    async def publish(
        self,
        event_type: str,
        event_data: dict[str, Any],
        *,
        redis: Redis | None = None,
        channel: str | None = None,
    ) -> None:
        payload = {
            "event_type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            **_jsonable(event_data),
        }
        client = redis or await self._client()
        await client.publish(channel or self.channel(event_type), json.dumps(payload))

    async def subscribe(self, event_type: str, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def listen(self) -> None:
        client = await self._client()
        pubsub = client.pubsub()
        channels = [self.channel(event_type) for event_type in self._handlers]
        if not channels:
            return
        await pubsub.subscribe(*channels)
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            data = json.loads(message["data"])
            event_type = data.get("event_type")
            for handler in self._handlers.get(event_type, []):
                await handler(data)

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
