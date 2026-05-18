"""Audit controller - thin dispatch layer."""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.audit import AuditEventDetailSchema, AuditStatsSchema, PaginatedAuditEvents, TimelineDataSchema
from app.schemas.auth import UserSchema
from app.services import audit_service


async def list_events(
    db: AsyncSession,
    *,
    user_id: str | None = None,
    event_type: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = None,
    sort: str = "created_at",
    order: str = "desc",
    page: int = 1,
    size: int = 25,
) -> PaginatedAuditEvents:
    return await audit_service.list_events(
        db,
        user_id=user_id,
        event_type=event_type,
        action=action,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
        q=q,
        sort=sort,
        order=order,
        page=page,
        size=size,
    )


async def get_event(db: AsyncSession, event_id: str) -> AuditEventDetailSchema:
    return await audit_service.get_event(db, event_id)


async def get_stats(db: AsyncSession, *, period: str = "today") -> AuditStatsSchema:
    return await audit_service.get_stats(db, period=period)


async def get_timeline(
    db: AsyncSession,
    *,
    user_id: str | None = None,
    event_type: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = None,
) -> TimelineDataSchema:
    return await audit_service.get_timeline(
        db,
        user_id=user_id,
        event_type=event_type,
        action=action,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )


async def export_log(
    db: AsyncSession,
    *,
    current_user: UserSchema,
    user_id: str | None = None,
    event_type: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = None,
) -> tuple[str, str]:
    return await audit_service.export_log(
        db,
        current_user=current_user,
        user_id=user_id,
        event_type=event_type,
        action=action,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )
