"""Audit service - internal audit trail logging, querying, and export."""

from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.generators.csv_generator import write_csv
from app.models.audit import AuditEventModel
from app.schemas.audit import (
    AuditEventDetailSchema,
    AuditEventSchema,
    AuditStatsSchema,
    PaginatedAuditEvents,
    TimelineDataSchema,
    TimelineGroupSchema,
)
from app.schemas.auth import UserSchema


def _utcnow() -> datetime:
    return datetime.utcnow()  # noqa: DTZ003


def _date_start(value: date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, time.min)


def _date_end(value: date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, time.max)


def _audit_user(current_user: UserSchema | None) -> dict[str, str]:
    if current_user is None:
        return {}
    return {"user_id": current_user.id, "user_name": current_user.name, "user_role": current_user.role}


def _filtered_stmt(
    *,
    user_id: str | None = None,
    event_type: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    date_from: date | datetime | None = None,
    date_to: date | datetime | None = None,
    q: str | None = None,
) -> Select[tuple[AuditEventModel]]:
    stmt = select(AuditEventModel)
    if user_id:
        stmt = stmt.where(AuditEventModel.user_id == user_id)
    if event_type:
        stmt = stmt.where(AuditEventModel.event_type == event_type.strip())
    if action:
        stmt = stmt.where(AuditEventModel.action == action.strip())
    if resource_type:
        stmt = stmt.where(AuditEventModel.resource_type == resource_type.strip())
    if date_from:
        stmt = stmt.where(AuditEventModel.created_at >= _date_start(date_from))
    if date_to:
        stmt = stmt.where(AuditEventModel.created_at <= _date_end(date_to))
    if q:
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(AuditEventModel.summary).like(like),
                func.lower(AuditEventModel.event_type).like(like),
                func.lower(AuditEventModel.resource_type).like(like),
                func.lower(AuditEventModel.user_name).like(like),
            )
        )
    return stmt


async def log(
    db: AsyncSession,
    *,
    event_type: str,
    action: str,
    resource_type: str,
    summary: str,
    resource_id: str | None = None,
    user_id: str | None = None,
    user_name: str | None = None,
    user_role: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    before_state: dict | None = None,
    after_state: dict | None = None,
    metadata: dict | None = None,
) -> None:
    """Insert an audit event record in the caller's transaction."""
    event = AuditEventModel(
        event_type=event_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        user_name=user_name or ("System" if user_id is None else None),
        user_role=user_role,
        ip_address=ip_address,
        user_agent=user_agent,
        summary=summary,
        before_state=before_state,
        after_state=after_state,
        metadata_=metadata,
    )
    db.add(event)
    await db.flush()


async def purge_old_events(db: AsyncSession, retention_days: int) -> int:
    """Delete audit events older than ``retention_days``. Returns deleted count."""
    cutoff = _utcnow() - timedelta(days=retention_days)
    result = await db.execute(delete(AuditEventModel).where(AuditEventModel.created_at < cutoff))
    return result.rowcount  # type: ignore[return-value]


async def list_events(
    db: AsyncSession,
    *,
    user_id: str | None = None,
    event_type: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    date_from: date | datetime | None = None,
    date_to: date | datetime | None = None,
    q: str | None = None,
    sort: str = "created_at",
    order: str = "desc",
    page: int = 1,
    size: int = 25,
) -> PaginatedAuditEvents:
    page = max(page, 1)
    size = min(max(size, 1), 100)
    base = _filtered_stmt(
        user_id=user_id,
        event_type=event_type,
        action=action,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )
    total = int((await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one() or 0)

    sort_columns = {
        "created_at": AuditEventModel.created_at,
        "event_type": AuditEventModel.event_type,
        "resource_type": AuditEventModel.resource_type,
        "action": AuditEventModel.action,
        "user_name": AuditEventModel.user_name,
    }
    sort_key = sort.lstrip("-").strip() or "created_at"
    sort_col = sort_columns.get(sort_key, AuditEventModel.created_at)
    descending = order.lower() != "asc" or sort.startswith("-")
    stmt = base.order_by(sort_col.desc() if descending else sort_col.asc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    return PaginatedAuditEvents(
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
        items=[AuditEventSchema.model_validate(event) for event in result.scalars().all()],
    )


async def get_event(db: AsyncSession, event_id: str) -> AuditEventDetailSchema:
    event = await db.get(AuditEventModel, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit event not found")
    return AuditEventDetailSchema.model_validate(event)


async def get_stats(db: AsyncSession, *, period: str = "today") -> AuditStatsSchema:
    start = datetime.combine(_utcnow().date(), time.min)
    if period == "7d":
        start = _utcnow() - timedelta(days=7)
    elif period == "30d":
        start = _utcnow() - timedelta(days=30)

    rows = (
        await db.execute(
            select(AuditEventModel.event_type, AuditEventModel.resource_type).where(AuditEventModel.created_at >= start)
        )
    ).all()
    return AuditStatsSchema(
        total_today=len(rows),
        login_events=sum(1 for event_type, _ in rows if str(event_type).startswith("auth.")),
        config_changes=sum(
            1 for event_type, resource_type in rows if resource_type == "config" or str(event_type).startswith("config.")
        ),
        rule_changes=sum(
            1 for event_type, resource_type in rows if resource_type == "rule" or str(event_type).startswith("rule.")
        ),
        warning_events=sum(
            1
            for event_type, resource_type in rows
            if resource_type == "warning" or str(event_type).startswith("warning.")
        ),
    )


async def get_timeline(
    db: AsyncSession,
    *,
    user_id: str | None = None,
    event_type: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    date_from: date | datetime | None = None,
    date_to: date | datetime | None = None,
    q: str | None = None,
    limit: int = 500,
) -> TimelineDataSchema:
    stmt = (
        _filtered_stmt(
            user_id=user_id,
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            date_from=date_from,
            date_to=date_to,
            q=q,
        )
        .order_by(AuditEventModel.created_at.desc())
        .limit(min(max(limit, 1), 2000))
    )
    events = (await db.execute(stmt)).scalars().all()
    grouped: dict[tuple[str | None, date], list[AuditEventModel]] = {}
    names: dict[tuple[str | None, date], str] = {}
    for event in events:
        key = (event.user_id, event.created_at.date())
        grouped.setdefault(key, []).append(event)
        names[key] = event.user_name or "System"
    groups = [
        TimelineGroupSchema(
            user_id=key[0],
            user_name=names[key],
            date=key[1],
            events=[AuditEventSchema.model_validate(event) for event in group_events],
        )
        for key, group_events in grouped.items()
    ]
    groups.sort(key=lambda group: (group.date, group.user_name), reverse=True)
    return TimelineDataSchema(groups=groups)


async def export_log(
    db: AsyncSession,
    *,
    current_user: UserSchema,
    user_id: str | None = None,
    event_type: str | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    date_from: date | datetime | None = None,
    date_to: date | datetime | None = None,
    q: str | None = None,
) -> tuple[str, str]:
    export_dir = Path(settings.BACKUPS_DIR) / "audit-exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    filename = f"audit-log-{_utcnow().strftime('%Y%m%d-%H%M%S')}.csv"
    file_path = export_dir / filename
    stmt = (
        _filtered_stmt(
            user_id=user_id,
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            date_from=date_from,
            date_to=date_to,
            q=q,
        )
        .order_by(AuditEventModel.created_at.desc())
        .limit(10000)
    )
    rows = (await db.execute(stmt)).scalars().all()
    await write_csv(
        str(file_path),
        [
            "created_at",
            "event_type",
            "action",
            "resource_type",
            "resource_id",
            "user_id",
            "user_name",
            "user_role",
            "ip_address",
            "summary",
        ],
        [
            {
                "created_at": event.created_at.isoformat(sep=" ", timespec="seconds"),
                "event_type": event.event_type,
                "action": event.action,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id or "",
                "user_id": event.user_id or "",
                "user_name": event.user_name or "System",
                "user_role": event.user_role or "",
                "ip_address": event.ip_address or "",
                "summary": event.summary,
            }
            for event in rows
        ],
    )
    await log(
        db,
        event_type="audit.exported",
        action="export",
        resource_type="audit",
        resource_id=filename,
        summary="Exported audit log",
        metadata={"row_count": len(rows), "filename": filename},
        **_audit_user(current_user),
    )
    return str(file_path), filename
