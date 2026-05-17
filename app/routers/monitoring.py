"""Live monitoring HTTP routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import monitoring_controller
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.auth import UserSchema
from app.schemas.common import MessageSchema
from app.schemas.devices import DeviceStatusSchema
from app.schemas.waste import SessionSummarySchema, WasteEntrySchema

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

MONITORING_READ_ROLES = ("super_admin", "institution_admin", "mess_admin", "analytics_viewer", "staff_operator")
MONITORING_WRITE_ROLES = ("super_admin", "institution_admin", "mess_admin", "staff_operator")


@router.get("/current-session", response_model=SessionSummarySchema)
async def get_current_session(
    device_id: UUID | None = Query(default=None),
    current_user: UserSchema = Depends(require_roles(*MONITORING_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await monitoring_controller.get_current_session(db, device_id=str(device_id) if device_id else None)


@router.get("/recent-entries", response_model=list[WasteEntrySchema])
async def get_recent_entries(
    device_id: UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: UserSchema = Depends(require_roles(*MONITORING_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await monitoring_controller.get_recent_entries(db, device_id=str(device_id) if device_id else None, limit=limit)


@router.get("/device-statuses", response_model=list[DeviceStatusSchema])
async def get_device_statuses(
    current_user: UserSchema = Depends(require_roles(*MONITORING_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await monitoring_controller.get_device_statuses(db)


@router.post("/alerts/{notif_id}/acknowledge", response_model=MessageSchema)
async def acknowledge_alert(
    notif_id: UUID,
    current_user: UserSchema = Depends(require_roles(*MONITORING_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    await monitoring_controller.acknowledge_alert(db, str(notif_id), current_user=current_user)
    return MessageSchema(message="Alert acknowledged")
