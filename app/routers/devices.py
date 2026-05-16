"""
Device router - Phase 2 device endpoints.

Ref: docs/plans/03-routes.md section 2. The restart route is intentionally
deferred to Phase 4 with the rule/command infrastructure.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import device_controller
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.auth import UserSchema
from app.schemas.common import MessageSchema
from app.schemas.devices import (
    DeviceCreateSchema,
    DeviceSchema,
    DeviceUpdateSchema,
    DeviceWithApiKeySchema,
    HealthDataSchema,
    HealthHistorySchema,
    PaginatedDevices,
    QueuedSyncSchema,
)

router = APIRouter(prefix="/devices", tags=["Devices"])

DEVICE_READ_ROLES = ("super_admin", "institution_admin", "mess_admin")
DEVICE_WRITE_ROLES = ("super_admin", "institution_admin")
DEVICE_SYNC_ROLES = ("super_admin", "institution_admin", "mess_admin")


@router.get("/", response_model=PaginatedDevices)
async def list_devices(
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: UserSchema = Depends(require_roles(*DEVICE_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await device_controller.list_devices(db, status_filter=status_filter, page=page, size=size)


@router.post("/", response_model=DeviceWithApiKeySchema, status_code=201)
async def register_device(
    body: DeviceCreateSchema,
    current_user: UserSchema = Depends(require_roles(*DEVICE_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await device_controller.register_device(db, body, current_user=current_user)


@router.get("/{device_id}", response_model=DeviceSchema)
async def get_device(
    device_id: UUID,
    current_user: UserSchema = Depends(require_roles(*DEVICE_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await device_controller.get_device(db, str(device_id))


@router.patch("/{device_id}", response_model=DeviceSchema)
async def update_device(
    device_id: UUID,
    body: DeviceUpdateSchema,
    current_user: UserSchema = Depends(require_roles(*DEVICE_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await device_controller.update_device(db, str(device_id), body, current_user=current_user)


@router.get("/{device_id}/health", response_model=HealthDataSchema)
async def get_device_health(
    device_id: UUID,
    current_user: UserSchema = Depends(require_roles(*DEVICE_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await device_controller.get_device_health(db, str(device_id))


@router.get("/{device_id}/health/history", response_model=HealthHistorySchema)
async def get_health_history(
    device_id: UUID,
    period: str = Query(default="24h"),
    current_user: UserSchema = Depends(require_roles(*DEVICE_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await device_controller.get_health_history(db, str(device_id), period)


@router.post("/{device_id}/sync", response_model=QueuedSyncSchema)
async def trigger_sync(
    device_id: UUID,
    current_user: UserSchema = Depends(require_roles(*DEVICE_SYNC_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await device_controller.trigger_sync(db, str(device_id), current_user=current_user)


@router.post("/{device_id}/decommission", response_model=MessageSchema)
async def decommission(
    device_id: UUID,
    current_user: UserSchema = Depends(require_roles(*DEVICE_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    await device_controller.decommission(db, str(device_id), current_user=current_user)
    return MessageSchema(message="Device decommissioned")
