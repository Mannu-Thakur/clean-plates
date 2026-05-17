"""WebSocket controller functions."""

from __future__ import annotations

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from app.schemas.auth import UserSchema
from app.services import ws_service


async def _stream_room(websocket: WebSocket, *, room: str, current_user: UserSchema) -> None:
    await ws_service.connect(websocket, room, current_user)
    try:
        while True:
            try:
                message = await websocket.receive_json()
            except ValueError:
                await ws_service.handle_client_message(websocket, {"type": "invalid_json"})
                continue
            await ws_service.handle_client_message(websocket, message)
    except WebSocketDisconnect:
        await ws_service.disconnect(websocket)
    finally:
        await ws_service.disconnect(websocket)


async def ws_dashboard(websocket: WebSocket, *, current_user: UserSchema) -> None:
    await _stream_room(websocket, room="dashboard", current_user=current_user)


async def ws_monitoring(websocket: WebSocket, *, current_user: UserSchema) -> None:
    await _stream_room(websocket, room="monitoring", current_user=current_user)
