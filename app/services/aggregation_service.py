"""Background aggregation, scoring, and status reconciliation for Phase 5."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone, tzinfo
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aggregated_waste import AggregatedWasteModel
from app.models.device import DeviceModel
from app.models.student import StudentMappingModel, StudentModel
from app.models.warning import PenaltyModel, WarningModel
from app.models.waste import WasteEntryModel
from app.services import config_service
from app.services.rule_event_service import dispatch_rule_event


_FALLBACK_TIMEZONES = {
    "Asia/Kolkata": timezone(timedelta(hours=5, minutes=30)),
    "Asia/Calcutta": timezone(timedelta(hours=5, minutes=30)),
    "UTC": UTC,
}


@dataclass(slots=True)
class AggregationRow:
    entry: WasteEntryModel
    mapping: StudentMappingModel | None


@dataclass(slots=True)
class WasteRecord:
    grams: float
    student_id: str
    local_hour: int


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def _institution_timezone(db: AsyncSession) -> tzinfo:
    config = await config_service.get_config(db, "institution")
    name = str(config.get("timezone") or "Asia/Kolkata")
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return _FALLBACK_TIMEZONES.get(name, UTC)


def _as_local(value: datetime, tz: tzinfo) -> datetime:
    """Convert a datetime to *tz*.  Naive values are assumed to be UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC).astimezone(tz)
    return value.astimezone(tz)


def _to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _entry_local_hour(entry: WasteEntryModel, tz: tzinfo) -> int:
    return _as_local(entry.timestamp, tz).hour


async def _load_rows_for_period(
    db: AsyncSession,
    *,
    session_date: date | None = None,
    start_local: datetime | None = None,
    end_local: datetime | None = None,
) -> list[AggregationRow]:
    stmt = (
        select(WasteEntryModel, StudentMappingModel)
        .join(StudentModel, WasteEntryModel.student_id == StudentModel.id)
        .outerjoin(StudentMappingModel, StudentMappingModel.student_id == StudentModel.id)
    )
    if session_date is not None:
        stmt = stmt.where(WasteEntryModel.session_date == session_date)
    if start_local is not None:
        stmt = stmt.where(WasteEntryModel.timestamp >= start_local.replace(tzinfo=None))
    if end_local is not None:
        stmt = stmt.where(WasteEntryModel.timestamp < end_local.replace(tzinfo=None))
    result = await db.execute(stmt)
    return [AggregationRow(entry=entry, mapping=mapping) for entry, mapping in result.all()]


def _records_for_entries(rows: list[AggregationRow], tz: tzinfo) -> list[WasteRecord]:
    return [
        WasteRecord(
            grams=float(row.entry.weight_grams),
            student_id=row.entry.student_id,
            local_hour=_entry_local_hour(row.entry, tz),
        )
        for row in rows
    ]


def _food_records(rows: list[AggregationRow], tz: tzinfo) -> dict[str, list[WasteRecord]]:
    buckets: dict[str, list[WasteRecord]] = defaultdict(list)
    for row in rows:
        items = row.entry.food_items or []
        names = [str(item.get("name") or "").strip() for item in items if str(item.get("name") or "").strip()]
        fallback_grams = float(row.entry.weight_grams) / len(names) if names else 0.0
        for item in items:
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            grams = item.get("grams")
            buckets[name].append(
                WasteRecord(
                    grams=float(grams) if grams is not None else fallback_grams,
                    student_id=row.entry.student_id,
                    local_hour=_entry_local_hour(row.entry, tz),
                )
            )
    return buckets


async def _upsert_aggregate(
    db: AsyncSession,
    *,
    period_type: str,
    period_start: datetime,
    period_end: datetime,
    scope_type: str,
    scope_id: str | None,
    records: list[WasteRecord],
) -> bool:
    if not records:
        return False

    total = sum(record.grams for record in records)
    count = len(records)
    hour_totals: dict[int, float] = defaultdict(float)
    for record in records:
        hour_totals[record.local_hour] += record.grams
    peak_hour = max(hour_totals.items(), key=lambda item: item[1])[0] if hour_totals else None

    stmt = select(AggregatedWasteModel).where(
        AggregatedWasteModel.period_type == period_type,
        AggregatedWasteModel.period_start == period_start,
        AggregatedWasteModel.scope_type == scope_type,
    )
    if scope_id is None:
        stmt = stmt.where(AggregatedWasteModel.scope_id.is_(None))
    else:
        stmt = stmt.where(AggregatedWasteModel.scope_id == scope_id)
    existing = (await db.execute(stmt)).scalar_one_or_none()

    values = {
        "period_end": period_end,
        "scope_id": scope_id,
        "total_waste_grams": float(total),
        "avg_waste_grams": float(total / count if count else 0.0),
        "entry_count": count,
        "student_count": len({record.student_id for record in records}),
        "peak_hour": peak_hour,
        "computed_at": _utcnow(),
    }
    if existing is None:
        db.add(
            AggregatedWasteModel(
                period_type=period_type,
                period_start=period_start,
                scope_type=scope_type,
                **values,
            )
        )
        return True

    for key, value in values.items():
        setattr(existing, key, value)
    return False


async def _aggregate_rows(
    db: AsyncSession,
    rows: list[AggregationRow],
    *,
    period_type: str,
    period_start: datetime,
    period_end: datetime,
    tz: tzinfo,
) -> int:
    writes = 0
    all_records = _records_for_entries(rows, tz)
    writes += int(
        await _upsert_aggregate(
            db,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            scope_type="global",
            scope_id=None,
            records=all_records,
        )
    )

    scoped: dict[tuple[str, str], list[WasteRecord]] = defaultdict(list)
    for row in rows:
        record = WasteRecord(
            grams=float(row.entry.weight_grams),
            student_id=row.entry.student_id,
            local_hour=_entry_local_hour(row.entry, tz),
        )
        scoped[("device", row.entry.device_id)].append(record)
        scoped[("student", row.entry.student_id)].append(record)
        scoped[("meal", row.entry.meal_type)].append(record)
        if row.mapping is not None:
            if row.mapping.branch:
                scoped[("branch", row.mapping.branch)].append(record)
            if row.mapping.hostel:
                scoped[("hostel", row.mapping.hostel)].append(record)

    for (scope_type, scope_id), records in scoped.items():
        writes += int(
            await _upsert_aggregate(
                db,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                scope_type=scope_type,
                scope_id=scope_id,
                records=records,
            )
        )

    for food_name, records in _food_records(rows, tz).items():
        writes += int(
            await _upsert_aggregate(
                db,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                scope_type="food_item",
                scope_id=food_name,
                records=records,
            )
        )
    await db.flush()
    return writes


async def run_hourly_aggregation(
    db: AsyncSession,
    *,
    now: datetime | None = None,
    force: bool = False,
) -> int:
    tz = await _institution_timezone(db)
    local_now = _as_local(now, tz) if now is not None else datetime.now(tz)
    if not force and local_now.minute not in (0, 30):
        return 0

    period_end_local = local_now.replace(minute=0, second=0, microsecond=0)
    period_start_local = period_end_local - timedelta(hours=1)
    rows = await _load_rows_for_period(db, start_local=period_start_local, end_local=period_end_local)
    return await _aggregate_rows(
        db,
        rows,
        period_type="hourly",
        period_start=_to_utc_naive(period_start_local),
        period_end=_to_utc_naive(period_end_local),
        tz=tz,
    )


async def run_daily_aggregation(
    db: AsyncSession,
    target_date: date | None = None,
    *,
    now: datetime | None = None,
    force: bool = False,
) -> int:
    tz = await _institution_timezone(db)
    local_now = _as_local(now, tz) if now is not None else datetime.now(tz)
    if target_date is None:
        if not force and (local_now.hour != 0 or local_now.minute != 0):
            return 0
        target_date = local_now.date() - timedelta(days=1)

    period_start_local = datetime.combine(target_date, time.min, tzinfo=tz)
    period_end_local = period_start_local + timedelta(days=1)
    rows = await _load_rows_for_period(db, session_date=target_date)
    return await _aggregate_rows(
        db,
        rows,
        period_type="daily",
        period_start=_to_utc_naive(period_start_local),
        period_end=_to_utc_naive(period_end_local),
        tz=tz,
    )


async def update_student_status(db: AsyncSession, student_id: str) -> str | None:
    student = await db.get(StudentModel, student_id)
    if student is None:
        return None

    total_result = await db.execute(
        select(func.coalesce(func.sum(WasteEntryModel.weight_grams), 0.0), func.count(WasteEntryModel.id)).where(
            WasteEntryModel.student_id == student_id
        )
    )
    total, entry_count = total_result.one()
    student.total_waste_grams = float(total or 0.0)
    student.avg_waste_grams = float(total or 0.0) / int(entry_count or 0) if entry_count else 0.0

    active_warnings = int(
        (
            await db.execute(
                select(func.count(WarningModel.id)).where(
                    WarningModel.student_id == student_id,
                    WarningModel.status == "active",
                )
            )
        ).scalar_one()
        or 0
    )
    active_penalties = int(
        (
            await db.execute(
                select(func.count(PenaltyModel.id)).where(
                    PenaltyModel.student_id == student_id,
                    PenaltyModel.status == "active",
                )
            )
        ).scalar_one()
        or 0
    )
    student.warning_count = active_warnings
    student.penalty_count = active_penalties

    if student.is_status_manual:
        await db.flush()
        return student.status

    thresholds = await config_service.get_config(db, "thresholds")
    warning_threshold = float(thresholds.get("warning_threshold_grams") or 100.0)
    waste_threshold = float(thresholds.get("waste_threshold_grams") or 150.0)
    penalty_threshold = float(thresholds.get("penalty_threshold_grams") or 200.0)

    if active_penalties > 0 or student.avg_waste_grams >= penalty_threshold:
        student.status = "red"
    elif active_warnings >= 3 or student.avg_waste_grams >= waste_threshold:
        student.status = "orange"
    elif active_warnings > 0 or student.avg_waste_grams >= warning_threshold:
        student.status = "yellow"
    else:
        student.status = "green"
    await db.flush()
    return student.status


async def _student_window_entries(
    db: AsyncSession,
    student_id: str,
    *,
    start_date: date,
    end_date: date,
) -> list[WasteEntryModel]:
    result = await db.execute(
        select(WasteEntryModel).where(
            WasteEntryModel.student_id == student_id,
            WasteEntryModel.session_date >= start_date,
            WasteEntryModel.session_date <= end_date,
        )
    )
    return list(result.scalars().all())


def _average(entries: list[WasteEntryModel]) -> float:
    return sum(float(entry.weight_grams) for entry in entries) / len(entries) if entries else 0.0


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


async def _compute_student_score(
    db: AsyncSession,
    student: StudentModel,
    *,
    today: date,
    thresholds: dict[str, Any],
) -> float:
    current_start = today - timedelta(days=29)
    previous_start = current_start - timedelta(days=30)
    previous_end = current_start - timedelta(days=1)

    current_entries = await _student_window_entries(db, student.id, start_date=current_start, end_date=today)
    previous_entries = await _student_window_entries(db, student.id, start_date=previous_start, end_date=previous_end)
    current_avg = _average(current_entries)
    previous_avg = _average(previous_entries)

    warning_threshold = float(thresholds.get("warning_threshold_grams") or 100.0)
    penalty_threshold = float(thresholds.get("penalty_threshold_grams") or 200.0)
    target_pct = float(thresholds.get("improvement_target_pct") or 25.0)

    if current_avg <= warning_threshold:
        avg_score = 100.0
    elif current_avg >= penalty_threshold:
        avg_score = 0.0
    else:
        avg_score = 100.0 - ((current_avg - warning_threshold) / (penalty_threshold - warning_threshold)) * 100.0

    if previous_avg <= 0:
        trend_score = 90.0 if current_avg <= warning_threshold else 65.0
    else:
        improvement = ((previous_avg - current_avg) / previous_avg) * 100.0
        trend_score = 50.0 + (improvement / max(target_pct, 1.0)) * 50.0

    discipline_score = 100.0 - (student.warning_count * 15.0) - (student.penalty_count * 35.0)

    if current_entries:
        high_count = sum(1 for entry in current_entries if entry.severity == "high")
        warning_count = sum(1 for entry in current_entries if entry.severity == "warning")
        severity_score = 100.0 - ((high_count / len(current_entries)) * 100.0) - (
            (warning_count / len(current_entries)) * 35.0
        )
        good_days = {
            entry.session_date
            for entry in current_entries
            if float(entry.weight_grams) <= warning_threshold
        }
        days_with_entries = {entry.session_date for entry in current_entries}
        consistency_score = (len(good_days) / len(days_with_entries)) * 100.0 if days_with_entries else 100.0
    else:
        severity_score = 100.0
        consistency_score = 100.0

    score = (
        _clamp_score(avg_score) * 0.35
        + _clamp_score(trend_score) * 0.20
        + _clamp_score(discipline_score) * 0.20
        + _clamp_score(severity_score) * 0.15
        + _clamp_score(consistency_score) * 0.10
    )
    return round(_clamp_score(score), 2)


async def compute_sustainability_scores(
    db: AsyncSession,
    *,
    now: datetime | None = None,
    force: bool = False,
) -> int:
    tz = await _institution_timezone(db)
    local_now = _as_local(now, tz) if now is not None else datetime.now(tz)
    if not force and (local_now.hour != 0 or local_now.minute != 15):
        return 0

    thresholds = await config_service.get_config(db, "thresholds")
    result = await db.execute(select(StudentModel).where(StudentModel.is_active.is_(True)))
    students = list(result.scalars().all())
    for student in students:
        await update_student_status(db, student.id)
        student.sustainability_score = await _compute_student_score(
            db,
            student,
            today=local_now.date(),
            thresholds=thresholds,
        )
    await db.flush()
    return len(students)


async def check_device_offline_status(db: AsyncSession, *, arq_pool=None) -> int:
    config = await config_service.get_config(db, "device")
    threshold_minutes = int(config.get("device_offline_threshold_minutes") or 10)
    now = _utcnow()
    cutoff = now - timedelta(minutes=threshold_minutes)

    result = await db.execute(
        select(DeviceModel).where(
            DeviceModel.is_deleted.is_(False),
            DeviceModel.status.notin_(("offline", "decommissioned")),
            DeviceModel.last_heartbeat.is_not(None),
            DeviceModel.last_heartbeat < cutoff,
        )
    )
    devices = list(result.scalars().all())
    for device in devices:
        offline_minutes = int((now - device.last_heartbeat).total_seconds() // 60) if device.last_heartbeat else 0
        await dispatch_rule_event(
            arq_pool,
            "device_offline",
            {
                "device_id": device.id,
                "device_serial": device.device_serial,
                "last_heartbeat": device.last_heartbeat,
                "offline_duration_minutes": offline_minutes,
            },
            depth=1,
        )
        device.status = "offline"
    await db.flush()
    return len(devices)
