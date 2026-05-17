"""WebSocket routes for live dashboard and monitoring streams."""

from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket

from app.controllers import ws_controller
from app.middleware.ws_auth import require_ws_roles
from app.schemas.auth import UserSchema

router = APIRouter(prefix="/ws", tags=["WebSockets"])

DASHBOARD_ROLES = ("super_admin", "institution_admin", "mess_admin", "analytics_viewer")
MONITORING_ROLES = ("super_admin", "institution_admin", "mess_admin", "analytics_viewer", "staff_operator")


@router.websocket("/dashboard")
async def ws_dashboard(
    websocket: WebSocket,
    current_user: UserSchema = Depends(require_ws_roles(*DASHBOARD_ROLES)),
):
    await ws_controller.ws_dashboard(websocket, current_user=current_user)


@router.websocket("/monitoring")
async def ws_monitoring(
    websocket: WebSocket,
    current_user: UserSchema = Depends(require_ws_roles(*MONITORING_ROLES)),
):
    await ws_controller.ws_monitoring(websocket, current_user=current_user)
