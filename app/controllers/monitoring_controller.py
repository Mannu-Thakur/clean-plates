"""Monitoring controller - thin dispatch layer over monitoring_service."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserSchema
from app.schemas.devices import DeviceStatusSchema
from app.schemas.waste import SessionSummarySchema, WasteEntrySchema
from app.services import monitoring_service


async def get_current_session(
    db: AsyncSession,
    *,
    device_id: str | None = None,
) -> SessionSummarySchema:
    return await monitoring_service.get_current_session(db, device_id=device_id)


async def get_recent_entries(
    db: AsyncSession,
    *,
    device_id: str | None = None,
    limit: int = 20,
) -> list[WasteEntrySchema]:
    return await monitoring_service.get_recent_entries(db, device_id=device_id, limit=limit)


async def get_device_statuses(db: AsyncSession) -> list[DeviceStatusSchema]:
    return await monitoring_service.get_device_statuses(db)


async def acknowledge_alert(db: AsyncSession, notification_id: str, *, current_user: UserSchema) -> None:
    await monitoring_service.acknowledge_alert(db, notification_id, current_user=current_user)
