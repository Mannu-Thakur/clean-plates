"""
Device service - registration, lookup, updates, and health reads.

Ref: docs/plans/02-controllers.md section 2.
"""

from __future__ import annotations

import json
import math
import re
from datetime import UTC, datetime, timedelta

from arq.connections import ArqRedis
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_api_key
from app.models.device import DeviceHealthModel, DeviceModel
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
from app.services import audit_service


_ALLOWED_STATUSES = {"online", "offline", "warning", "decommissioned"}
_PERIOD_RE = re.compile(r"^(?P<count>\d+)(?P<unit>[hd])$")


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _device_state(device: DeviceModel) -> dict:
    return {
        "id": device.id,
        "device_serial": device.device_serial,
        "edge_node_name": device.edge_node_name,
        "institution_name": device.institution_name,
        "institution_code": device.institution_code,
        "campus_name": device.campus_name,
        "mess_name": device.mess_name,
        "mess_id": device.mess_id,
        "hostel_name": device.hostel_name,
        "hostel_block": device.hostel_block,
        "floor_number": device.floor_number,
        "capacity": device.capacity,
        "status": device.status,
        "is_deleted": device.is_deleted,
    }


def _audit_user(current_user: UserSchema | None) -> dict:
    if current_user is None:
        return {}
    return {
        "user_id": current_user.id,
        "user_name": current_user.name,
        "user_role": current_user.role,
    }


def _parse_period(period: str) -> tuple[str, datetime]:
    normalized = (period or "24h").strip().lower()
    match = _PERIOD_RE.match(normalized)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period must use '<number>h' or '<number>d', for example '24h' or '7d'",
        )

    count = int(match.group("count"))
    unit = match.group("unit")
    if count <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="period must be greater than zero")

    if unit == "h":
        if count > 24 * 365:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="period is too large")
        delta = timedelta(hours=count)
    else:
        if count > 365:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="period is too large")
        delta = timedelta(days=count)

    return normalized, _utcnow() - delta


async def _get_device_or_404(db: AsyncSession, device_id: str, *, include_deleted: bool = False) -> DeviceModel:
    stmt = select(DeviceModel).where(DeviceModel.id == device_id)
    if not include_deleted:
        stmt = stmt.where(DeviceModel.is_deleted.is_(False))

    result = await db.execute(stmt)
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


async def list_devices(
    db: AsyncSession,
    *,
    status_filter: str | None = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedDevices:
    page = max(page, 1)
    size = min(max(size, 1), 100)

    filters = []
    if status_filter:
        status_value = status_filter.strip().lower()
        if status_value not in _ALLOWED_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid device status filter")
        filters.append(DeviceModel.status == status_value)
        if status_value != "decommissioned":
            filters.append(DeviceModel.is_deleted.is_(False))
    else:
        filters.append(DeviceModel.is_deleted.is_(False))

    total_result = await db.execute(select(func.count()).select_from(DeviceModel).where(*filters))
    total = int(total_result.scalar_one() or 0)

    result = await db.execute(
        select(DeviceModel)
        .where(*filters)
        .order_by(DeviceModel.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    devices = result.scalars().all()

    return PaginatedDevices(
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
        items=[DeviceSchema.model_validate(device) for device in devices],
    )


async def register_device(
    db: AsyncSession,
    body: DeviceCreateSchema,
    *,
    current_user: UserSchema | None = None,
) -> DeviceWithApiKeySchema:
    serial = body.device_serial.strip()
    existing_result = await db.execute(select(DeviceModel).where(DeviceModel.device_serial == serial))
    existing = existing_result.scalar_one_or_none()
    if existing and not existing.is_deleted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Device serial is already registered")
    if existing and existing.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device serial belongs to a decommissioned device; restore or use a new serial",
        )

    raw_api_key, api_key_hash = generate_api_key()
    data = body.model_dump()
    data["device_serial"] = serial
    device = DeviceModel(
        **data,
        status="online",
        active_since=_utcnow(),
        api_key_hash=api_key_hash,
        is_deleted=False,
    )
    db.add(device)
    await db.flush()

    await audit_service.log(
        db,
        event_type="device.registered",
        action="create",
        resource_type="device",
        resource_id=device.id,
        summary=f"Registered device '{device.device_serial}'",
        after_state=_device_state(device),
        **_audit_user(current_user),
    )

    schema = DeviceSchema.model_validate(device).model_dump()
    return DeviceWithApiKeySchema(**schema, api_key=raw_api_key)


async def get_device(db: AsyncSession, device_id: str) -> DeviceSchema:
    device = await _get_device_or_404(db, device_id, include_deleted=True)
    return DeviceSchema.model_validate(device)


async def update_device(
    db: AsyncSession,
    device_id: str,
    body: DeviceUpdateSchema,
    *,
    current_user: UserSchema | None = None,
) -> DeviceSchema:
    device = await _get_device_or_404(db, device_id)
    data = body.model_dump(exclude_unset=True)
    for field in ("edge_node_name", "mess_name"):
        if field in data and data[field] is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{field} cannot be null")

    if not data:
        return DeviceSchema.model_validate(device)

    before = _device_state(device)
    for field, value in data.items():
        setattr(device, field, value)
    await db.flush()

    await audit_service.log(
        db,
        event_type="device.updated",
        action="update",
        resource_type="device",
        resource_id=device.id,
        summary=f"Updated device '{device.device_serial}'",
        before_state=before,
        after_state=_device_state(device),
        **_audit_user(current_user),
    )
    return DeviceSchema.model_validate(device)


async def get_device_health(db: AsyncSession, device_id: str) -> HealthDataSchema:
    await _get_device_or_404(db, device_id)
    result = await db.execute(
        select(DeviceHealthModel)
        .where(DeviceHealthModel.device_id == device_id)
        .order_by(DeviceHealthModel.recorded_at.desc())
        .limit(1)
    )
    health = result.scalar_one_or_none()
    if health is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No health data available for this device")
    return HealthDataSchema.model_validate(health)


async def get_health_history(db: AsyncSession, device_id: str, period: str = "24h") -> HealthHistorySchema:
    await _get_device_or_404(db, device_id)
    normalized_period, cutoff = _parse_period(period)
    result = await db.execute(
        select(DeviceHealthModel)
        .where(DeviceHealthModel.device_id == device_id, DeviceHealthModel.recorded_at >= cutoff)
        .order_by(DeviceHealthModel.recorded_at.asc())
    )
    rows = result.scalars().all()
    return HealthHistorySchema(
        device_id=device_id,
        period=normalized_period,
        data=[HealthDataSchema.model_validate(row) for row in rows],
    )


async def trigger_sync(
    db: AsyncSession,
    device_id: str,
    *,
    current_user: UserSchema | None = None,
) -> QueuedSyncSchema:
    device = await _get_device_or_404(db, device_id)
    if device.status == "decommissioned":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot sync a decommissioned device")

    await audit_service.log(
        db,
        event_type="device.sync_requested",
        action="sync",
        resource_type="device",
        resource_id=device.id,
        summary=f"Manual sync requested for device '{device.device_serial}'",
        metadata={"pending_count": 0},
        **_audit_user(current_user),
    )
    return QueuedSyncSchema(
        message="Device queued for sync",
        pending_count=0,
        device_id=device.id,
    )


async def restart_service(
    db: AsyncSession,
    device_id: str,
    *,
    current_user: UserSchema | None = None,
    arq_pool: ArqRedis | None = None,
) -> None:
    device = await _get_device_or_404(db, device_id)
    if device.status == "decommissioned":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot restart a decommissioned device")
    if arq_pool is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis command bus is unavailable")

    channel = f"cleanplates:devices:{device.id}:commands"
    payload = {
        "command": "restart",
        "device_id": device.id,
        "device_serial": device.device_serial,
        "requested_at": _utcnow().isoformat(),
        "requested_by": str(current_user.id) if current_user else None,
    }
    await arq_pool.publish(channel, json.dumps(payload))

    await audit_service.log(
        db,
        event_type="device.restart_requested",
        action="restart",
        resource_type="device",
        resource_id=device.id,
        summary=f"Restart requested for device '{device.device_serial}'",
        metadata={"delivery": "redis_pubsub", "channel": channel, "command": "restart"},
        **_audit_user(current_user),
    )


async def decommission(
    db: AsyncSession,
    device_id: str,
    *,
    current_user: UserSchema | None = None,
) -> None:
    device = await _get_device_or_404(db, device_id, include_deleted=True)
    if device.status == "decommissioned" or device.is_deleted:
        return

    before = _device_state(device)
    device.status = "decommissioned"
    device.is_deleted = True
    await db.flush()

    await audit_service.log(
        db,
        event_type="device.decommissioned",
        action="decommission",
        resource_type="device",
        resource_id=device.id,
        summary=f"Decommissioned device '{device.device_serial}'",
        before_state=before,
        after_state=_device_state(device),
        **_audit_user(current_user),
    )
