"""
Device controller - thin dispatch layer over device_service.

Ref: docs/plans/02-controllers.md section 2.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserSchema
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
from app.services import device_service


async def list_devices(
    db: AsyncSession,
    *,
    status_filter: str | None = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedDevices:
    return await device_service.list_devices(db, status_filter=status_filter, page=page, size=size)


async def register_device(
    db: AsyncSession,
    body: DeviceCreateSchema,
    *,
    current_user: UserSchema,
) -> DeviceWithApiKeySchema:
    return await device_service.register_device(db, body, current_user=current_user)


async def get_device(db: AsyncSession, device_id: str) -> DeviceSchema:
    return await device_service.get_device(db, device_id)


async def update_device(
    db: AsyncSession,
    device_id: str,
    body: DeviceUpdateSchema,
    *,
    current_user: UserSchema,
) -> DeviceSchema:
    return await device_service.update_device(db, device_id, body, current_user=current_user)


async def get_device_health(db: AsyncSession, device_id: str) -> HealthDataSchema:
    return await device_service.get_device_health(db, device_id)


async def get_health_history(db: AsyncSession, device_id: str, period: str = "24h") -> HealthHistorySchema:
    return await device_service.get_health_history(db, device_id, period)


async def trigger_sync(
    db: AsyncSession,
    device_id: str,
    *,
    current_user: UserSchema,
) -> QueuedSyncSchema:
    return await device_service.trigger_sync(db, device_id, current_user=current_user)


async def decommission(
    db: AsyncSession,
    device_id: str,
    *,
    current_user: UserSchema,
) -> None:
    await device_service.decommission(db, device_id, current_user=current_user)
