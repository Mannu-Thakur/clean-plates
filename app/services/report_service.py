"""Report generation, storage, and schedule service."""

from __future__ import annotations

import math
import os
from datetime import UTC, date, datetime, time, timedelta, tzinfo
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from arq.connections import ArqRedis
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.generators.csv_generator import write_csv
from app.generators.excel_generator import write_excel
from app.generators.pdf_generator import write_pdf
from app.models.report import ReportModel, ReportScheduleModel
from app.models.student import StudentMappingModel
from app.models.waste import WasteEntryModel
from app.schemas.auth import UserSchema
from app.schemas.reports import (
    PaginatedReports,
    ReportConfigSchema,
    ReportScheduleSchema,
    ReportSchema,
    ScheduleCreateSchema,
    ScheduleUpdateSchema,
)
from app.services import audit_service, config_service, notification_service


_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _audit_user(current_user: UserSchema | None) -> dict:
    if current_user is None:
        return {}
    return {"user_id": current_user.id, "user_name": current_user.name, "user_role": current_user.role}


def _report_ext(report_format: str) -> str:
    return "xlsx" if report_format == "excel" else report_format


def _reports_dir() -> Path:
    path = Path(settings.REPORTS_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def _institution_tz(db: AsyncSession) -> tzinfo:
    institution = await config_service.get_config(db, "institution")
    timezone_name = str(institution.get("timezone") or "Asia/Kolkata")
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return UTC


def _parse_time(value: str) -> time:
    hour, minute = value.split(":", 1)
    hour_int = int(hour)
    minute_int = int(minute)
    if not 0 <= hour_int <= 23 or not 0 <= minute_int <= 59:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="time_of_day must be HH:MM")
    return time(hour_int, minute_int)


def _next_month_first(day: date) -> date:
    if day.month == 12:
        return day.replace(year=day.year + 1, month=1, day=1)
    return day.replace(month=day.month + 1, day=1)


async def calculate_next_run(db: AsyncSession, schedule: ReportScheduleModel | ScheduleCreateSchema) -> datetime | None:
    active = schedule.active
    if not active:
        return None
    tz = await _institution_tz(db)
    now_local = datetime.now(UTC).astimezone(tz)
    run_time = _parse_time(schedule.time_of_day)

    if schedule.frequency == "daily":
        candidate_date = now_local.date()
        candidate = datetime.combine(candidate_date, run_time, tzinfo=tz)
        if candidate <= now_local:
            candidate = candidate + timedelta(days=1)
    elif schedule.frequency == "weekly":
        target_weekday = _WEEKDAYS.get((schedule.day_of_week or "monday").lower(), 0)
        days_ahead = (target_weekday - now_local.weekday()) % 7
        candidate = datetime.combine(now_local.date() + timedelta(days=days_ahead), run_time, tzinfo=tz)
        if candidate <= now_local:
            candidate = candidate + timedelta(days=7)
    elif schedule.frequency == "monthly":
        candidate = datetime.combine(now_local.date().replace(day=1), run_time, tzinfo=tz)
        if candidate <= now_local:
            candidate = datetime.combine(_next_month_first(now_local.date()), run_time, tzinfo=tz)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="frequency must be daily, weekly, or monthly")

    return candidate.astimezone(UTC).replace(tzinfo=None)


def _report_state(report: ReportModel) -> dict[str, Any]:
    return {
        "id": report.id,
        "type": report.type,
        "format": report.format,
        "status": report.status,
        "file_path": report.file_path,
        "file_size": report.file_size,
    }


def _schedule_state(schedule: ReportScheduleModel) -> dict[str, Any]:
    return {
        "id": schedule.id,
        "report_type": schedule.report_type,
        "format": schedule.format,
        "frequency": schedule.frequency,
        "day_of_week": schedule.day_of_week,
        "time_of_day": schedule.time_of_day,
        "auto_email": schedule.auto_email,
        "active": schedule.active,
        "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
    }


async def _report_rows(db: AsyncSession, config: dict[str, Any]) -> list[dict[str, Any]]:
    date_from = config.get("date_from")
    date_to = config.get("date_to")
    student_id = config.get("student_id")
    filters = dict(config.get("filters") or {})
    stmt = (
        select(WasteEntryModel, StudentMappingModel)
        .outerjoin(StudentMappingModel, StudentMappingModel.student_id == WasteEntryModel.student_id)
        .order_by(WasteEntryModel.timestamp.desc())
    )
    if date_from:
        stmt = stmt.where(WasteEntryModel.session_date >= date.fromisoformat(str(date_from)))
    if date_to:
        stmt = stmt.where(WasteEntryModel.session_date <= date.fromisoformat(str(date_to)))
    if student_id:
        stmt = stmt.where(WasteEntryModel.student_id == str(student_id))
    if filters.get("meal_type"):
        stmt = stmt.where(WasteEntryModel.meal_type == str(filters["meal_type"]).strip().lower())
    if filters.get("device_id"):
        stmt = stmt.where(WasteEntryModel.device_id == str(filters["device_id"]))
    result = await db.execute(stmt.limit(5000))
    rows: list[dict[str, Any]] = []
    for entry, mapping in result.all():
        rows.append(
            {
                "timestamp": entry.timestamp.isoformat(sep=" ", timespec="seconds"),
                "session_date": entry.session_date.isoformat(),
                "student_id": entry.student_id,
                "student_name": mapping.name if mapping else "",
                "student_device_id": mapping.device_id if mapping else "",
                "meal_type": entry.meal_type,
                "weight_grams": round(float(entry.weight_grams), 2),
                "severity": entry.severity,
            }
        )
    return rows


async def _report_payload(db: AsyncSession, report: ReportModel) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    config = dict(report.config or {})
    rows = await _report_rows(db, config)
    total_grams = sum(float(row["weight_grams"]) for row in rows)
    title = f"{report.type.replace('_', ' ').title()} Report"
    summary = {
        "report_id": report.id,
        "type": report.type,
        "format": report.format,
        "generated_at_utc": _utcnow().isoformat(sep=" ", timespec="seconds"),
        "entries": len(rows),
        "total_waste_grams": round(total_grams, 2),
        "average_waste_grams": round(total_grams / len(rows), 2) if rows else 0.0,
    }
    return title, summary, rows


async def _write_report_file(db: AsyncSession, report: ReportModel) -> int:
    title, summary, rows = await _report_payload(db, report)
    headers = list(rows[0].keys()) if rows else [
        "timestamp",
        "session_date",
        "student_id",
        "student_name",
        "student_device_id",
        "meal_type",
        "weight_grams",
        "severity",
    ]
    if report.format == "csv":
        return await write_csv(report.file_path, headers, rows)
    if report.format == "excel":
        return await write_excel(report.file_path, headers, rows)
    return await write_pdf(report.file_path, title, summary, rows)


async def list_reports(
    db: AsyncSession,
    *,
    type_filter: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedReports:
    page = max(page, 1)
    size = min(max(size, 1), 100)
    stmt = select(ReportModel)
    count_stmt = select(func.count(ReportModel.id))
    if type_filter:
        stmt = stmt.where(ReportModel.type == type_filter.strip().lower())
        count_stmt = count_stmt.where(ReportModel.type == type_filter.strip().lower())
    if date_from:
        stmt = stmt.where(func.date(ReportModel.created_at) >= date_from.isoformat())
        count_stmt = count_stmt.where(func.date(ReportModel.created_at) >= date_from.isoformat())
    if date_to:
        stmt = stmt.where(func.date(ReportModel.created_at) <= date_to.isoformat())
        count_stmt = count_stmt.where(func.date(ReportModel.created_at) <= date_to.isoformat())
    total = int((await db.execute(count_stmt)).scalar_one() or 0)
    result = await db.execute(stmt.order_by(ReportModel.created_at.desc()).offset((page - 1) * size).limit(size))
    return PaginatedReports(
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
        items=[ReportSchema.model_validate(report) for report in result.scalars().all()],
    )


async def generate_report(
    db: AsyncSession,
    body: ReportConfigSchema,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> ReportSchema:
    config = body.model_dump(mode="json")
    report = ReportModel(
        type=body.type,
        format=body.format,
        file_path="",
        file_size=None,
        config=config,
        generated_by=current_user.id,
        status="pending",
    )
    db.add(report)
    await db.flush()
    report.file_path = str(_reports_dir() / f"{report.id}.{_report_ext(report.format)}")
    await db.flush()
    await audit_service.log(
        db,
        event_type="report.queued",
        action="create",
        resource_type="report",
        resource_id=report.id,
        summary=f"Queued {report.type} report",
        after_state=_report_state(report),
        **_audit_user(current_user),
    )
    await db.commit()
    if arq_pool is not None:
        await arq_pool.enqueue_job("generate_report_task", report.id)
    else:
        await generate_report_file(db, report.id)
        await db.commit()
    return ReportSchema.model_validate(report)


async def generate_report_file(db: AsyncSession, report_id: str) -> ReportModel:
    report = await db.get(ReportModel, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if report.status == "ready" and os.path.exists(report.file_path):
        return report
    report.status = "generating"
    report.error_message = None
    await db.flush()
    try:
        report.file_size = await _write_report_file(db, report)
        report.status = "ready"
        report.generated_at = _utcnow()
    except Exception as exc:
        report.status = "failed"
        report.error_message = str(exc)[:500]
        raise
    finally:
        await db.flush()
    return report


async def get_report_file(db: AsyncSession, report_id: str) -> tuple[str, str]:
    report = await db.get(ReportModel, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if report.status != "ready":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Report is not ready")
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file is missing")
    return report.file_path, Path(report.file_path).name


async def delete_report(db: AsyncSession, report_id: str, *, current_user: UserSchema) -> None:
    report = await db.get(ReportModel, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    before = _report_state(report)
    if report.file_path and os.path.exists(report.file_path):
        os.remove(report.file_path)
    await db.delete(report)
    await db.flush()
    await audit_service.log(
        db,
        event_type="report.deleted",
        action="delete",
        resource_type="report",
        resource_id=report_id,
        summary="Deleted report",
        before_state=before,
        **_audit_user(current_user),
    )


async def list_schedules(db: AsyncSession) -> list[ReportScheduleSchema]:
    result = await db.execute(select(ReportScheduleModel).order_by(ReportScheduleModel.created_at.desc()))
    return [ReportScheduleSchema.model_validate(schedule) for schedule in result.scalars().all()]


async def create_schedule(
    db: AsyncSession,
    body: ScheduleCreateSchema,
    *,
    current_user: UserSchema,
) -> ReportScheduleSchema:
    schedule = ReportScheduleModel(
        report_type=body.report_type,
        format=body.format,
        frequency=body.frequency,
        day_of_week=body.day_of_week,
        time_of_day=body.time_of_day,
        email_recipients=body.email_recipients,
        auto_email=body.auto_email,
        active=body.active,
        created_by=current_user.id,
    )
    schedule.next_run = await calculate_next_run(db, schedule)
    db.add(schedule)
    await db.flush()
    await audit_service.log(
        db,
        event_type="report_schedule.created",
        action="create",
        resource_type="report_schedule",
        resource_id=schedule.id,
        summary=f"Created {schedule.frequency} report schedule",
        after_state=_schedule_state(schedule),
        **_audit_user(current_user),
    )
    return ReportScheduleSchema.model_validate(schedule)


async def update_schedule(
    db: AsyncSession,
    schedule_id: str,
    body: ScheduleUpdateSchema,
    *,
    current_user: UserSchema,
) -> ReportScheduleSchema:
    schedule = await db.get(ReportScheduleModel, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report schedule not found")
    before = _schedule_state(schedule)
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(schedule, key, value)
    schedule.next_run = await calculate_next_run(db, schedule)
    await db.flush()
    await audit_service.log(
        db,
        event_type="report_schedule.updated",
        action="update",
        resource_type="report_schedule",
        resource_id=schedule.id,
        summary="Updated report schedule",
        before_state=before,
        after_state=_schedule_state(schedule),
        **_audit_user(current_user),
    )
    return ReportScheduleSchema.model_validate(schedule)


async def delete_schedule(db: AsyncSession, schedule_id: str, *, current_user: UserSchema) -> None:
    schedule = await db.get(ReportScheduleModel, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report schedule not found")
    before = _schedule_state(schedule)
    await db.delete(schedule)
    await db.flush()
    await audit_service.log(
        db,
        event_type="report_schedule.deleted",
        action="delete",
        resource_type="report_schedule",
        resource_id=schedule_id,
        summary="Deleted report schedule",
        before_state=before,
        **_audit_user(current_user),
    )


async def execute_scheduled_reports(db: AsyncSession, *, arq_pool: ArqRedis | None = None) -> int:
    result = await db.execute(
        select(ReportScheduleModel).where(
            ReportScheduleModel.active.is_(True),
            ReportScheduleModel.next_run.is_not(None),
            ReportScheduleModel.next_run <= _utcnow(),
        )
    )
    schedules = result.scalars().all()
    for schedule in schedules:
        config = ReportConfigSchema(type=schedule.report_type, format=schedule.format)
        report = ReportModel(
            type=config.type,
            format=config.format,
            file_path="",
            file_size=None,
            config=config.model_dump(mode="json"),
            generated_by=schedule.created_by,
            status="pending",
        )
        db.add(report)
        await db.flush()
        report.file_path = str(_reports_dir() / f"{report.id}.{_report_ext(report.format)}")
        await generate_report_file(db, report.id)
        schedule.last_run = _utcnow()
        schedule.next_run = await calculate_next_run(db, schedule)

        if schedule.auto_email and schedule.email_recipients:
            created = await notification_service.create_system_notification(
                db,
                notif_type="system",
                channel="email",
                subject=f"Scheduled report ready: {report.type}",
                body=f"<p>Your scheduled {report.type} report is ready. Report ID: {report.id}</p>",
                recipient_type="individual",
                recipient_ids=list(schedule.email_recipients),
                related_entity_type="report",
                related_entity_id=report.id,
            )
            if created.recipient_count:
                await notification_service.dispatch_notification(db, created.notification.id)
    return len(schedules)
