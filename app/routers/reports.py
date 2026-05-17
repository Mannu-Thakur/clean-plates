"""Report generation and scheduling routes."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import report_controller
from app.core.redis import get_arq_pool
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.auth import UserSchema
from app.schemas.common import MessageSchema
from app.schemas.reports import (
    PaginatedReports,
    ReportConfigSchema,
    ReportScheduleSchema,
    ReportSchema,
    ScheduleCreateSchema,
    ScheduleUpdateSchema,
)

router = APIRouter(prefix="/reports", tags=["Reports"])

REPORT_READ_ROLES = ("super_admin", "institution_admin", "mess_admin", "analytics_viewer")
REPORT_WRITE_ROLES = ("super_admin", "institution_admin", "mess_admin")


@router.get("/", response_model=PaginatedReports)
async def list_reports(
    type_filter: str | None = Query(default=None, alias="type"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: UserSchema = Depends(require_roles(*REPORT_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await report_controller.list_reports(
        db, type_filter=type_filter, date_from=date_from, date_to=date_to, page=page, size=size
    )


@router.post("/generate", response_model=ReportSchema, status_code=201)
async def generate_report(
    body: ReportConfigSchema,
    current_user: UserSchema = Depends(require_roles(*REPORT_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
    arq_pool: ArqRedis | None = Depends(get_arq_pool),
):
    return await report_controller.generate_report(db, body, current_user=current_user, arq_pool=arq_pool)


@router.get("/schedules", response_model=list[ReportScheduleSchema])
async def list_schedules(
    current_user: UserSchema = Depends(require_roles(*REPORT_WRITE_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await report_controller.list_schedules(db)


@router.post("/schedules", response_model=ReportScheduleSchema, status_code=201)
async def create_schedule(
    body: ScheduleCreateSchema,
    current_user: UserSchema = Depends(require_roles(*REPORT_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await report_controller.create_schedule(db, body, current_user=current_user)


@router.patch("/schedules/{schedule_id}", response_model=ReportScheduleSchema)
async def update_schedule(
    schedule_id: UUID,
    body: ScheduleUpdateSchema,
    current_user: UserSchema = Depends(require_roles(*REPORT_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await report_controller.update_schedule(db, str(schedule_id), body, current_user=current_user)


@router.delete("/schedules/{schedule_id}", response_model=MessageSchema)
async def delete_schedule(
    schedule_id: UUID,
    current_user: UserSchema = Depends(require_roles(*REPORT_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    await report_controller.delete_schedule(db, str(schedule_id), current_user=current_user)
    return MessageSchema(message="Report schedule deleted")


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    current_user: UserSchema = Depends(require_roles(*REPORT_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    file_path, filename = await report_controller.download_report(db, str(report_id))
    return FileResponse(file_path, filename=filename)


@router.delete("/{report_id}", response_model=MessageSchema)
async def delete_report(
    report_id: UUID,
    current_user: UserSchema = Depends(require_roles(*REPORT_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    await report_controller.delete_report(db, str(report_id), current_user=current_user)
    return MessageSchema(message="Report deleted")
