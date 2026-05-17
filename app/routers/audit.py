"""Audit log routes."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import audit_controller
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.audit import AuditEventDetailSchema, AuditStatsSchema, PaginatedAuditEvents, TimelineDataSchema
from app.schemas.auth import UserSchema

router = APIRouter(prefix="/audit", tags=["Audit"])

AUDIT_READ_ROLES = ("super_admin", "institution_admin")


@router.get("/", response_model=PaginatedAuditEvents)
async def list_events(
    user_id: UUID | None = Query(default=None),
    event_type: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    q: str | None = Query(default=None),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),
    current_user: UserSchema = Depends(require_roles(*AUDIT_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await audit_controller.list_events(
        db,
        user_id=str(user_id) if user_id else None,
        event_type=event_type,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
        q=q,
        sort=sort,
        order=order,
        page=page,
        size=size,
    )


@router.get("/stats", response_model=AuditStatsSchema)
async def get_stats(
    period: str = Query(default="today", pattern="^(today|7d|30d)$"),
    current_user: UserSchema = Depends(require_roles(*AUDIT_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await audit_controller.get_stats(db, period=period)


@router.get("/timeline", response_model=TimelineDataSchema)
async def get_timeline(
    user_id: UUID | None = Query(default=None),
    event_type: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    q: str | None = Query(default=None),
    current_user: UserSchema = Depends(require_roles(*AUDIT_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await audit_controller.get_timeline(
        db,
        user_id=str(user_id) if user_id else None,
        event_type=event_type,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )


@router.get("/export")
async def export_log(
    user_id: UUID | None = Query(default=None),
    event_type: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    q: str | None = Query(default=None),
    format: str = Query(default="csv"),  # noqa: A002
    current_user: UserSchema = Depends(require_roles(*AUDIT_READ_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    if format != "csv":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only csv export is supported")
    file_path, filename = await audit_controller.export_log(
        db,
        current_user=current_user,
        user_id=str(user_id) if user_id else None,
        event_type=event_type,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )
    return FileResponse(file_path, filename=filename, media_type="text/csv")


@router.get("/{event_id}", response_model=AuditEventDetailSchema)
async def get_event(
    event_id: UUID,
    current_user: UserSchema = Depends(require_roles(*AUDIT_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await audit_controller.get_event(db, str(event_id))
