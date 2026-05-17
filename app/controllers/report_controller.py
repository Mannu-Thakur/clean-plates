"""Report controller - thin dispatch layer."""

from __future__ import annotations

from datetime import date

from arq.connections import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserSchema
from app.schemas.reports import (
    PaginatedReports,
    ReportConfigSchema,
    ReportScheduleSchema,
    ReportSchema,
    ScheduleCreateSchema,
    ScheduleUpdateSchema,
)
from app.services import report_service


async def list_reports(
    db: AsyncSession,
    *,
    type_filter: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedReports:
    return await report_service.list_reports(
        db, type_filter=type_filter, date_from=date_from, date_to=date_to, page=page, size=size
    )


async def generate_report(
    db: AsyncSession,
    body: ReportConfigSchema,
    *,
    current_user: UserSchema,
    arq_pool: ArqRedis | None = None,
) -> ReportSchema:
    return await report_service.generate_report(db, body, current_user=current_user, arq_pool=arq_pool)


async def download_report(db: AsyncSession, report_id: str) -> tuple[str, str]:
    return await report_service.get_report_file(db, report_id)


async def delete_report(db: AsyncSession, report_id: str, *, current_user: UserSchema) -> None:
    await report_service.delete_report(db, report_id, current_user=current_user)


async def list_schedules(db: AsyncSession) -> list[ReportScheduleSchema]:
    return await report_service.list_schedules(db)


async def create_schedule(
    db: AsyncSession,
    body: ScheduleCreateSchema,
    *,
    current_user: UserSchema,
) -> ReportScheduleSchema:
    return await report_service.create_schedule(db, body, current_user=current_user)


async def update_schedule(
    db: AsyncSession,
    schedule_id: str,
    body: ScheduleUpdateSchema,
    *,
    current_user: UserSchema,
) -> ReportScheduleSchema:
    return await report_service.update_schedule(db, schedule_id, body, current_user=current_user)


async def delete_schedule(db: AsyncSession, schedule_id: str, *, current_user: UserSchema) -> None:
    await report_service.delete_schedule(db, schedule_id, current_user=current_user)
