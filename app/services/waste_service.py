"""
Waste service - ML ingestion, waste entry reads, and live session summaries.

Ref: docs/plans/02-controllers.md sections 4 and 15.
"""

from __future__ import annotations

import math
import os
import uuid
from datetime import UTC, date, datetime, time, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.device import DeviceHealthModel, DeviceModel
from app.models.student import StudentMappingModel, StudentModel
from app.models.waste import WasteEntryModel
from app.schemas.common import LogoUrlSchema
from app.schemas.waste import (
    BulkWasteIngestSchema,
    HeartbeatPayload,
    PaginatedEntries,
    SessionSummarySchema,
    SyncResultSchema,
    WasteEntryCreateSchema,
    WasteEntryDetailSchema,
    WasteEntrySchema,
)
from app.services import config_service


_IMAGE_EXTENSIONS_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
_MAX_PLATE_IMAGE_BYTES = 10 * 1024 * 1024
_UPLOAD_CHUNK_SIZE = 64 * 1024
_FALLBACK_TIMEZONES = {
    "Asia/Kolkata": timezone(timedelta(hours=5, minutes=30)),
    "Asia/Calcutta": timezone(timedelta(hours=5, minutes=30)),
    "UTC": UTC,
}


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _normalize_db_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


async def _institution_timezone(db: AsyncSession) -> tzinfo:
    config = await config_service.get_config(db, "institution")
    name = str(config.get("timezone") or "Asia/Kolkata")
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return _FALLBACK_TIMEZONES.get(name, UTC)


def _localize_timestamp(timestamp: datetime, timezone: tzinfo) -> datetime:
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone)
    return timestamp.astimezone(timezone)


def _parse_clock(value: str) -> time:
    hour, minute = value.split(":", maxsplit=1)
    return time(hour=int(hour), minute=int(minute))


def _time_in_window(value: time, start: time, end: time) -> bool:
    if start <= end:
        return start <= value <= end
    return value >= start or value <= end


def _meal_display_name(meal: dict) -> str:
    return str(meal.get("display_name") or meal.get("name") or "Other").strip() or "Other"


async def _resolve_meal(
    db: AsyncSession,
    *,
    provided_meal_type: str | None,
    timestamp: datetime,
) -> tuple[str, str, str, str, bool]:
    if provided_meal_type:
        meal_type = provided_meal_type.strip().lower()
        return meal_type, meal_type.replace("_", " ").title(), "", "", True

    timezone = await _institution_timezone(db)
    local_timestamp = _localize_timestamp(timestamp, timezone)
    current_time = local_timestamp.time()
    meals_config = await config_service.get_config(db, "meals")
    timings = meals_config.get("timings") or []

    for meal in timings:
        if not meal.get("is_active", True):
            continue
        try:
            start = _parse_clock(str(meal["start_time"]))
            end = _parse_clock(str(meal["end_time"]))
        except (KeyError, TypeError, ValueError):
            continue
        if _time_in_window(current_time, start, end):
            name = str(meal.get("name") or "other").strip().lower() or "other"
            return name, _meal_display_name(meal), str(meal["start_time"]), str(meal["end_time"]), True

    return "other", "Other", "", "", False


async def _classify_severity(db: AsyncSession, weight_grams: float) -> str:
    thresholds = await config_service.get_config(db, "thresholds")
    warning_threshold = float(thresholds.get("warning_threshold_grams") or 100.0)
    high_threshold = float(thresholds.get("waste_threshold_grams") or 150.0)
    if weight_grams >= high_threshold:
        return "high"
    if weight_grams >= warning_threshold:
        return "warning"
    return "normal"


async def _resolve_device(db: AsyncSession, device_serial: str) -> DeviceModel:
    serial = device_serial.strip()
    result = await db.execute(
        select(DeviceModel).where(
            DeviceModel.device_serial == serial,
            DeviceModel.is_deleted.is_(False),
            DeviceModel.status != "decommissioned",
        )
    )
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device serial not registered")
    return device


async def _ensure_authenticated_device(device: DeviceModel, authenticated_device: DeviceModel | None) -> None:
    if authenticated_device is None:
        return
    if authenticated_device.id != device.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Payload device_serial does not match the authenticated API key",
        )


async def _get_or_create_student(db: AsyncSession, student_device_id: str) -> StudentModel:
    card_id = student_device_id.strip()
    result = await db.execute(select(StudentModel).where(StudentModel.device_id == card_id))
    student = result.scalar_one_or_none()
    if student is not None:
        return student

    student = StudentModel(device_id=card_id)
    try:
        async with db.begin_nested():
            db.add(student)
            await db.flush()
    except IntegrityError as exc:
        result = await db.execute(select(StudentModel).where(StudentModel.device_id == card_id))
        concurrent_student = result.scalar_one_or_none()
        if concurrent_student is not None:
            return concurrent_student
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Could not create student card stub") from exc
    return student


async def _refresh_student_waste_metrics(db: AsyncSession, student_id: str) -> None:
    result = await db.execute(
        select(func.coalesce(func.sum(WasteEntryModel.weight_grams), 0.0), func.count(WasteEntryModel.id)).where(
            WasteEntryModel.student_id == student_id
        )
    )
    total, count = result.one()
    avg = float(total) / int(count) if count else 0.0
    student = await db.get(StudentModel, student_id)
    if student is not None:
        student.total_waste_grams = float(total)
        student.avg_waste_grams = avg
        student.sustainability_score = max(0.0, min(100.0, 100.0 - (avg / 3.0)))


def _food_item_dicts(body: WasteEntryCreateSchema) -> list[dict]:
    return [item.model_dump() for item in body.food_items]


def _entry_schema(
    entry: WasteEntryModel,
    *,
    student_device_id: str,
    student_name: str | None = None,
    detail: bool = False,
) -> WasteEntrySchema | WasteEntryDetailSchema:
    payload = {
        "id": entry.id,
        "student_id": entry.student_id,
        "device_id": entry.device_id,
        "weight_grams": entry.weight_grams,
        "meal_type": entry.meal_type,
        "food_items": entry.food_items or [],
        "severity": entry.severity,
        "session_date": entry.session_date,
        "timestamp": entry.timestamp,
        "student_name": student_name,
        "student_device_id": student_device_id,
    }
    if detail:
        return WasteEntryDetailSchema(
            **payload,
            confidence_score=entry.confidence_score,
            plate_image_path=entry.plate_image_path,
            rule_evaluated=entry.rule_evaluated,
        )
    return WasteEntrySchema(**payload)


async def _entry_row(db: AsyncSession, entry_id: str):
    result = await db.execute(
        select(WasteEntryModel, StudentModel.device_id, StudentMappingModel.name)
        .join(StudentModel, WasteEntryModel.student_id == StudentModel.id)
        .outerjoin(StudentMappingModel, StudentMappingModel.student_id == StudentModel.id)
        .where(WasteEntryModel.id == entry_id)
    )
    return result.one_or_none()


async def create_waste_entry(
    db: AsyncSession,
    body: WasteEntryCreateSchema,
    *,
    authenticated_device: DeviceModel | None = None,
    source: str = "ml",
) -> WasteEntrySchema:
    device = await _resolve_device(db, body.device_serial)
    await _ensure_authenticated_device(device, authenticated_device)
    student = await _get_or_create_student(db, body.student_device_id)
    storage_timestamp = _normalize_db_timestamp(body.timestamp)
    timezone = await _institution_timezone(db)
    session_date = _localize_timestamp(body.timestamp, timezone).date()
    meal_type, _, _, _, _ = await _resolve_meal(db, provided_meal_type=body.meal_type, timestamp=body.timestamp)
    severity = await _classify_severity(db, body.weight_grams)

    entry = WasteEntryModel(
        student_id=student.id,
        device_id=device.id,
        weight_grams=body.weight_grams,
        meal_type=meal_type,
        food_items=_food_item_dicts(body),
        confidence_score=body.confidence_score,
        plate_image_path=body.plate_image_path,
        session_date=session_date,
        timestamp=storage_timestamp,
        severity=severity,
        rule_evaluated=False,
        source=source,
    )
    try:
        async with db.begin_nested():
            db.add(entry)
            await db.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Waste entry already exists") from exc

    await _refresh_student_waste_metrics(db, student.id)
    row = await _entry_row(db, entry.id)
    if row is None:
        return _entry_schema(entry, student_device_id=student.device_id)
    saved_entry, student_device_id, student_name = row
    return _entry_schema(saved_entry, student_device_id=student_device_id, student_name=student_name)


async def bulk_sync(
    db: AsyncSession,
    body: BulkWasteIngestSchema,
    *,
    authenticated_device: DeviceModel | None = None,
) -> SyncResultSchema:
    inserted = 0
    skipped = 0
    errors: list[dict] = []

    for index, payload in enumerate(body.entries, start=1):
        try:
            device = await _resolve_device(db, payload.device_serial)
            await _ensure_authenticated_device(device, authenticated_device)
            storage_timestamp = _normalize_db_timestamp(payload.timestamp)
            duplicate_result = await db.execute(
                select(WasteEntryModel.id).where(
                    WasteEntryModel.device_id == device.id,
                    WasteEntryModel.timestamp == storage_timestamp,
                )
            )
            if duplicate_result.scalar_one_or_none() is not None:
                skipped += 1
                continue

            await create_waste_entry(db, payload, authenticated_device=authenticated_device, source="sync")
            inserted += 1
        except HTTPException as exc:
            if exc.status_code == status.HTTP_409_CONFLICT:
                skipped += 1
            else:
                errors.append(
                    {
                        "index": index,
                        "device_serial": payload.device_serial,
                        "student_device_id": payload.student_device_id,
                        "error": exc.detail,
                    }
                )
        except Exception as exc:  # pragma: no cover - defensive per-entry isolation
            errors.append(
                {
                    "index": index,
                    "device_serial": payload.device_serial,
                    "student_device_id": payload.student_device_id,
                    "error": str(exc),
                }
            )

    if authenticated_device is not None:
        authenticated_device.last_sync = _utcnow()
    return SyncResultSchema(
        total_received=len(body.entries),
        inserted=inserted,
        skipped=skipped,
        errors=errors,
    )


async def get_entry(db: AsyncSession, entry_id: str) -> WasteEntryDetailSchema:
    row = await _entry_row(db, entry_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Waste entry not found")
    entry, student_device_id, student_name = row
    return _entry_schema(entry, student_device_id=student_device_id, student_name=student_name, detail=True)


def _apply_entry_filters(
    stmt,
    *,
    student_id: str | None = None,
    device_id: str | None = None,
    meal_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    if student_id:
        stmt = stmt.where(WasteEntryModel.student_id == student_id)
    if device_id:
        stmt = stmt.where(WasteEntryModel.device_id == device_id)
    if meal_type:
        stmt = stmt.where(WasteEntryModel.meal_type == meal_type.strip().lower())
    if date_from:
        stmt = stmt.where(WasteEntryModel.session_date >= date_from)
    if date_to:
        stmt = stmt.where(WasteEntryModel.session_date <= date_to)
    return stmt


async def list_entries(
    db: AsyncSession,
    *,
    student_id: str | None = None,
    device_id: str | None = None,
    meal_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedEntries:
    page = max(page, 1)
    size = min(max(size, 1), 100)

    count_stmt = select(func.count(WasteEntryModel.id))
    count_stmt = _apply_entry_filters(
        count_stmt,
        student_id=student_id,
        device_id=device_id,
        meal_type=meal_type,
        date_from=date_from,
        date_to=date_to,
    )
    total_result = await db.execute(count_stmt)
    total = int(total_result.scalar_one() or 0)

    stmt = (
        select(WasteEntryModel, StudentModel.device_id, StudentMappingModel.name)
        .join(StudentModel, WasteEntryModel.student_id == StudentModel.id)
        .outerjoin(StudentMappingModel, StudentMappingModel.student_id == StudentModel.id)
    )
    stmt = _apply_entry_filters(
        stmt,
        student_id=student_id,
        device_id=device_id,
        meal_type=meal_type,
        date_from=date_from,
        date_to=date_to,
    )
    stmt = stmt.order_by(WasteEntryModel.timestamp.desc(), WasteEntryModel.id.asc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    rows = result.all()

    return PaginatedEntries(
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
        items=[
            _entry_schema(entry, student_device_id=student_device_id, student_name=student_name)
            for entry, student_device_id, student_name in rows
        ],
    )


async def get_current_session(db: AsyncSession, *, device_id: str | None = None) -> SessionSummarySchema:
    timezone = await _institution_timezone(db)
    now_local = datetime.now(timezone)
    meal_type, session_name, start_time, end_time, is_active = await _resolve_meal(
        db,
        provided_meal_type=None,
        timestamp=now_local,
    )

    filters = [
        WasteEntryModel.session_date == now_local.date(),
        WasteEntryModel.meal_type == meal_type,
    ]
    if device_id:
        filters.append(WasteEntryModel.device_id == device_id)

    result = await db.execute(
        select(func.count(WasteEntryModel.id), func.coalesce(func.sum(WasteEntryModel.weight_grams), 0.0)).where(
            *filters
        )
    )
    count, total = result.one()
    return SessionSummarySchema(
        session_name=session_name,
        meal_type=meal_type,
        start_time=start_time,
        end_time=end_time,
        entry_count_today=int(count or 0),
        total_waste_today_grams=float(total or 0.0),
        is_active=is_active,
    )


async def get_recent_entries(
    db: AsyncSession,
    *,
    device_id: str | None = None,
    limit: int = 20,
) -> list[WasteEntrySchema]:
    limit = min(max(limit, 1), 100)
    stmt = (
        select(WasteEntryModel, StudentModel.device_id, StudentMappingModel.name)
        .join(StudentModel, WasteEntryModel.student_id == StudentModel.id)
        .outerjoin(StudentMappingModel, StudentMappingModel.student_id == StudentModel.id)
    )
    if device_id:
        stmt = stmt.where(WasteEntryModel.device_id == device_id)
    stmt = stmt.order_by(WasteEntryModel.timestamp.desc(), WasteEntryModel.id.asc()).limit(limit)
    result = await db.execute(stmt)
    return [
        _entry_schema(entry, student_device_id=student_device_id, student_name=student_name)
        for entry, student_device_id, student_name in result.all()
    ]


async def ml_heartbeat(
    db: AsyncSession,
    payload: HeartbeatPayload,
    *,
    device: DeviceModel,
) -> None:
    device.last_heartbeat = _utcnow()
    device.status = "online"
    db.add(
        DeviceHealthModel(
            device_id=device.id,
            cpu_percent=payload.cpu_percent,
            ram_percent=payload.ram_percent,
            temperature=payload.temperature,
            storage_percent=payload.storage_percent,
            connectivity=payload.connectivity,
            recorded_at=_utcnow(),
        )
    )
    await db.flush()


async def upload_image(
    image_file: UploadFile,
    *,
    content_length: int | None = None,
) -> LogoUrlSchema:
    if content_length is not None and content_length > _MAX_PLATE_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image is larger than 10MB")

    content_type = (image_file.content_type or "").lower()
    extension = _IMAGE_EXTENSIONS_BY_TYPE.get(content_type)
    if extension is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only JPEG, PNG, and WebP images are supported")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"plate_{uuid.uuid4().hex}{extension}"
    absolute_path = os.path.join(settings.UPLOAD_DIR, filename)

    bytes_read = 0
    try:
        with open(absolute_path, "wb") as output:
            while chunk := await image_file.read(_UPLOAD_CHUNK_SIZE):
                bytes_read += len(chunk)
                if bytes_read > _MAX_PLATE_IMAGE_BYTES:
                    output.close()
                    try:
                        os.remove(absolute_path)
                    except FileNotFoundError:
                        pass
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Image is larger than 10MB",
                    )
                output.write(chunk)
    finally:
        await image_file.close()

    if bytes_read == 0:
        try:
            os.remove(absolute_path)
        except FileNotFoundError:
            pass
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image file is empty")

    return LogoUrlSchema(logo_url=f"/static/uploads/{filename}")
