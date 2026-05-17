"""
WebSocket connection management and Redis fan-out.

Each Uvicorn worker owns only its local client sockets. Redis Pub/Sub carries
room broadcasts and domain events to every worker so multi-worker deployments
still deliver live dashboard updates.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from app.core.config import settings
from app.schemas.auth import UserSchema

logger = logging.getLogger("cleanplates.websocket")

ROOMS = ("dashboard", "monitoring")
EVENT_ROUTES: dict[str, tuple[tuple[str, str], ...]] = {
    "waste_entry_created": (("monitoring", "waste_entry"),),
    "warning_issued": (("dashboard", "warning_issued"), ("monitoring", "alert")),
    "penalty_applied": (("dashboard", "alert"), ("monitoring", "alert")),
    "rule_executed": (("dashboard", "rule_executed"),),
    "device_heartbeat": (("monitoring", "device_status"),),
    "device_offline": (("monitoring", "device_status"), ("dashboard", "alert")),
}

_ROOM_CHANNEL_PREFIX = "cleanplates:ws:"
_USER_CHANNEL = "cleanplates:ws:users"
_EVENT_CHANNEL_PREFIX = "cleanplates:events:"
_LIVE_QUEUE_LIMIT = 100


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set | deque):
        return [_jsonable(item) for item in value]
    return value


def _room_channel(room: str) -> str:
    return f"{_ROOM_CHANNEL_PREFIX}{room}"


def _event_channel(event_type: str) -> str:
    return f"{_EVENT_CHANNEL_PREFIX}{event_type}"


def _clean_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(payload or {})
    cleaned.setdefault("timestamp", _utc_timestamp())
    return _jsonable(cleaned)


def _payload_data(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key not in {"type", "event_type", "timestamp", "depth", "data"}
    }


def _event_payload(ws_type: str, event_type: str, event: dict[str, Any]) -> dict[str, Any]:
    data = _payload_data(event)
    payload: dict[str, Any] = {
        "type": ws_type,
        "event_type": event_type,
        "timestamp": event.get("timestamp") or _utc_timestamp(),
        "data": data,
        **data,
    }
    if ws_type == "alert":
        payload.setdefault("alert_type", event_type)
    return _clean_payload(payload)


def _message_channel(message: dict[str, Any]) -> str:
    channel = message.get("channel")
    if isinstance(channel, bytes):
        return channel.decode()
    return str(channel or "")


def _decode_message_data(message: dict[str, Any]) -> dict[str, Any] | None:
    data = message.get("data")
    if isinstance(data, bytes):
        data = data.decode()
    if isinstance(data, str):
        try:
            decoded = json.loads(data)
        except json.JSONDecodeError:
            logger.warning("Discarding non-JSON WebSocket Pub/Sub payload")
            return None
    elif isinstance(data, dict):
        decoded = data
    else:
        return None
    return _clean_payload(decoded)


def _payload_value(payload: dict[str, Any], key: str) -> Any:
    if key in payload:
        return payload[key]
    data = payload.get("data")
    if isinstance(data, dict):
        return data.get(key)
    return None


def _matches_filters(payload: dict[str, Any], filters: dict[str, Any]) -> bool:
    if not filters:
        return True
    for key, expected in filters.items():
        if expected in (None, "", "all", "*"):
            continue
        actual = _payload_value(payload, key)
        if actual is None:
            continue
        if str(actual).lower() != str(expected).lower():
            return False
    return True


@dataclass(slots=True)
class ConnectionState:
    user_id: str
    role: str
    room: str
    paused: bool = False
    filters: dict[str, Any] = field(default_factory=dict)
    queued: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=_LIVE_QUEUE_LIMIT))


class ConnectionManager:
    """Tracks local WebSocket connections and publishes broadcasts to Redis."""

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._users: dict[str, set[WebSocket]] = defaultdict(set)
        self._states: dict[WebSocket, ConnectionState] = {}
        self._publisher: Redis | None = None
        self._lock = asyncio.Lock()

    async def _publisher_client(self) -> Redis:
        if self._publisher is None:
            self._publisher = Redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
                health_check_interval=30,
            )
        return self._publisher

    async def connect(self, websocket: WebSocket, room: str, current_user: UserSchema) -> None:
        if room not in ROOMS:
            await websocket.close(code=4000, reason="Unknown room")
            return
        await websocket.accept()
        async with self._lock:
            state = ConnectionState(user_id=str(current_user.id), role=current_user.role, room=room)
            self._states[websocket] = state
            self._rooms[room].add(websocket)
            self._users[state.user_id].add(websocket)
        await self._safe_send(
            websocket,
            {"type": "connected", "room": room, "user_id": str(current_user.id), "timestamp": _utc_timestamp()},
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            state = self._states.pop(websocket, None)
            if state is None:
                return
            self._rooms[state.room].discard(websocket)
            if not self._rooms[state.room]:
                self._rooms.pop(state.room, None)
            self._users[state.user_id].discard(websocket)
            if not self._users[state.user_id]:
                self._users.pop(state.user_id, None)

    async def broadcast_to_room(
        self,
        room: str,
        payload: dict[str, Any],
        *,
        redis: Redis | None = None,
    ) -> None:
        if room not in ROOMS:
            raise ValueError(f"Unknown WebSocket room: {room}")
        message = _clean_payload(payload)
        message.setdefault("room", room)
        try:
            client = redis or await self._publisher_client()
            await client.publish(_room_channel(room), json.dumps(message))
        except (RedisConnectionError, RedisError, OSError):
            logger.warning("Redis publish failed for room %s; falling back to local sockets", room, exc_info=True)
            await self._deliver_to_room(room, message)

    async def send_to_user(
        self,
        user_id: str,
        payload: dict[str, Any],
        *,
        redis: Redis | None = None,
    ) -> None:
        message = _clean_payload({**payload, "target_user_id": str(user_id)})
        try:
            client = redis or await self._publisher_client()
            await client.publish(_USER_CHANNEL, json.dumps(message))
        except (RedisConnectionError, RedisError, OSError):
            logger.warning("Redis publish failed for user %s; falling back to local sockets", user_id, exc_info=True)
            await self._deliver_to_user(str(user_id), message)

    async def handle_client_message(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        message_type = str(message.get("type") or "").lower()
        if message_type in {"ping", "heartbeat"}:
            await self._safe_send(websocket, {"type": "pong", "timestamp": _utc_timestamp()})
            return
        if message_type == "pause":
            await self._set_paused(websocket, True)
            await self._safe_send(websocket, {"type": "ack", "action": "pause", "timestamp": _utc_timestamp()})
            return
        if message_type == "resume":
            queued = await self._set_paused(websocket, False)
            await self._safe_send(
                websocket,
                {"type": "ack", "action": "resume", "queued_count": len(queued), "timestamp": _utc_timestamp()},
            )
            for payload in queued:
                await self._safe_send(websocket, payload)
            return
        if message_type in {"filter", "set_filter"}:
            filters = message.get("filters")
            if not isinstance(filters, dict):
                filters = {
                    key: value
                    for key, value in message.items()
                    if key in {"meal_type", "device_id", "severity", "alert_type"}
                }
            await self._set_filters(websocket, filters)
            await self._safe_send(
                websocket,
                {"type": "ack", "action": "filter", "filters": filters, "timestamp": _utc_timestamp()},
            )
            return
        if message_type == "clear_filter":
            await self._set_filters(websocket, {})
            await self._safe_send(websocket, {"type": "ack", "action": "clear_filter", "timestamp": _utc_timestamp()})
            return
        await self._safe_send(
            websocket,
            {"type": "error", "message": "Unsupported WebSocket command", "timestamp": _utc_timestamp()},
        )

    async def _set_paused(self, websocket: WebSocket, paused: bool) -> list[dict[str, Any]]:
        async with self._lock:
            state = self._states.get(websocket)
            if state is None:
                return []
            state.paused = paused
            if paused:
                return []
            queued = list(state.queued)
            state.queued.clear()
            return queued

    async def _set_filters(self, websocket: WebSocket, filters: dict[str, Any]) -> None:
        async with self._lock:
            state = self._states.get(websocket)
            if state is not None:
                state.filters = dict(filters)

    async def _deliver_to_room(self, room: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self._rooms.get(room, set()))
        for websocket in sockets:
            await self._send_if_allowed(websocket, payload)

    async def _deliver_to_user(self, user_id: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self._users.get(user_id, set()))
        for websocket in sockets:
            await self._send_if_allowed(websocket, payload)

    async def _send_if_allowed(self, websocket: WebSocket, payload: dict[str, Any]) -> None:
        async with self._lock:
            state = self._states.get(websocket)
            if state is None:
                return
            if not _matches_filters(payload, state.filters):
                return
            if state.paused:
                state.queued.append(payload)
                return
        await self._safe_send(websocket, payload)

    async def _safe_send(self, websocket: WebSocket, payload: dict[str, Any]) -> None:
        if websocket.application_state != WebSocketState.CONNECTED:
            await self.disconnect(websocket)
            return
        try:
            await websocket.send_json(_clean_payload(payload))
        except (RuntimeError, WebSocketDisconnect):
            await self.disconnect(websocket)

    async def _fanout_event(self, event_type: str, event: dict[str, Any]) -> None:
        for room, ws_type in EVENT_ROUTES.get(event_type, ()):
            await self._deliver_to_room(room, _event_payload(ws_type, event_type, event))

    async def _handle_pubsub_message(self, message: dict[str, Any]) -> None:
        if message.get("type") != "message":
            return
        channel = _message_channel(message)
        payload = _decode_message_data(message)
        if payload is None:
            return

        if channel == _USER_CHANNEL:
            target_user_id = str(payload.get("target_user_id") or "")
            if target_user_id:
                await self._deliver_to_user(target_user_id, payload)
            return

        if channel.startswith(_ROOM_CHANNEL_PREFIX):
            room = channel.removeprefix(_ROOM_CHANNEL_PREFIX)
            if room in ROOMS:
                await self._deliver_to_room(room, payload)
            return

        if channel.startswith(_EVENT_CHANNEL_PREFIX):
            event_type = str(payload.get("event_type") or channel.removeprefix(_EVENT_CHANNEL_PREFIX))
            await self._fanout_event(event_type, payload)

    async def subscriber_loop(self) -> None:
        channels = [_room_channel(room) for room in ROOMS]
        channels.append(_USER_CHANNEL)
        channels.extend(_event_channel(event_type) for event_type in EVENT_ROUTES)

        while True:
            redis: Redis | None = None
            pubsub = None
            try:
                redis = Redis.from_url(self.redis_url, decode_responses=True, health_check_interval=30)
                pubsub = redis.pubsub(ignore_subscribe_messages=True)
                await pubsub.subscribe(*channels)
                logger.info("WebSocket Redis subscriber listening on %s channels", len(channels))
                async for message in pubsub.listen():
                    await self._handle_pubsub_message(message)
            except asyncio.CancelledError:
                raise
            except (RedisConnectionError, RedisError, OSError):
                logger.warning("WebSocket Redis subscriber disconnected; retrying in 2s", exc_info=True)
                await asyncio.sleep(2)
            finally:
                if pubsub is not None:
                    try:
                        await pubsub.aclose()
                    except Exception:  # pragma: no cover - defensive cleanup
                        logger.debug("Could not close WebSocket pubsub cleanly", exc_info=True)
                if redis is not None:
                    try:
                        await redis.aclose()
                    except Exception:  # pragma: no cover - defensive cleanup
                        logger.debug("Could not close WebSocket Redis client cleanly", exc_info=True)

    async def close(self) -> None:
        if self._publisher is not None:
            await self._publisher.aclose()
            self._publisher = None

    def counts(self) -> dict[str, int]:
        return {room: len(sockets) for room, sockets in self._rooms.items()}


manager = ConnectionManager(settings.REDIS_URL)


async def connect(websocket: WebSocket, room: str, current_user: UserSchema) -> None:
    await manager.connect(websocket, room, current_user)


async def disconnect(websocket: WebSocket) -> None:
    await manager.disconnect(websocket)


async def broadcast_to_room(room: str, payload: dict[str, Any], *, redis: Redis | None = None) -> None:
    await manager.broadcast_to_room(room, payload, redis=redis)


async def send_to_user(user_id: str, payload: dict[str, Any], *, redis: Redis | None = None) -> None:
    await manager.send_to_user(user_id, payload, redis=redis)


async def handle_client_message(websocket: WebSocket, message: dict[str, Any]) -> None:
    await manager.handle_client_message(websocket, message)


async def subscriber_loop() -> None:
    await manager.subscriber_loop()


async def close() -> None:
    await manager.close()
