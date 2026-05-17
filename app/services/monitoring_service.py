"""Live monitoring read models and alert acknowledgement."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import DeviceHealthModel, DeviceModel
from app.schemas.auth import UserSchema
from app.schemas.devices import DeviceStatusSchema
from app.schemas.waste import SessionSummarySchema, WasteEntrySchema
from app.services import config_service, notification_service, waste_service


def _aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _health_status(
    device: DeviceModel,
    health: DeviceHealthModel | None,
    *,
    offline_cutoff: datetime,
) -> str:
    if device.status == "decommissioned":
        return "decommissioned"
    last_heartbeat = _aware_utc(device.last_heartbeat)
    if device.status == "offline" or last_heartbeat is None or last_heartbeat < offline_cutoff:
        return "offline"
    if health is None:
        return device.status or "online"
    if not health.connectivity:
        return "offline"
    high_load = health.cpu_percent >= 90 or health.ram_percent >= 90
    high_storage = health.storage_percent is not None and health.storage_percent >= 90
    high_temp = health.temperature is not None and health.temperature >= 75
    if high_load or high_storage or high_temp:
        return "warning"
    return device.status or "online"


async def get_current_session(
    db: AsyncSession,
    *,
    device_id: str | None = None,
) -> SessionSummarySchema:
    return await waste_service.get_current_session(db, device_id=device_id)


async def get_recent_entries(
    db: AsyncSession,
    *,
    device_id: str | None = None,
    limit: int = 20,
) -> list[WasteEntrySchema]:
    return await waste_service.get_recent_entries(db, device_id=device_id, limit=limit)


async def get_device_statuses(db: AsyncSession) -> list[DeviceStatusSchema]:
    config = await config_service.get_config(db, "device")
    threshold_minutes = int(config.get("device_offline_threshold_minutes") or 10)
    offline_cutoff = datetime.now(UTC) - timedelta(minutes=threshold_minutes)

    result = await db.execute(
        select(DeviceModel)
        .where(DeviceModel.is_deleted.is_(False))
        .order_by(DeviceModel.mess_name.asc(), DeviceModel.edge_node_name.asc())
    )
    devices = result.scalars().all()
    statuses: list[DeviceStatusSchema] = []
    for device in devices:
        health_result = await db.execute(
            select(DeviceHealthModel)
            .where(DeviceHealthModel.device_id == device.id)
            .order_by(DeviceHealthModel.recorded_at.desc(), DeviceHealthModel.id.desc())
            .limit(1)
        )
        health = health_result.scalar_one_or_none()
        statuses.append(
            DeviceStatusSchema(
                id=device.id,
                edge_node_name=device.edge_node_name,
                mess_name=device.mess_name,
                status=_health_status(device, health, offline_cutoff=offline_cutoff),
                cpu_percent=health.cpu_percent if health else None,
                ram_percent=health.ram_percent if health else None,
                temperature=health.temperature if health else None,
                last_heartbeat=device.last_heartbeat,
            )
        )
    return statuses


async def acknowledge_alert(db: AsyncSession, notification_id: str, *, current_user: UserSchema) -> None:
    await notification_service.mark_read(db, notification_id, current_user=current_user)
