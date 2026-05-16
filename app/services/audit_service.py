"""
Audit service — internal audit trail logging and purge.

Phase 1 implements ``log()`` and ``purge_old_events()`` only.
All read endpoints are added in Phase 8.

Ref: 02-controllers.md §14
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEventModel


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
    """Insert an audit event record.

    ``current_user`` can be None for system/background actions — treated as
    "System" action per Cross-Cutting Rules.
    """
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
    # Flush so the audit record is included in the caller's transaction
    await db.flush()


async def purge_old_events(db: AsyncSession, retention_days: int) -> int:
    """Delete audit events older than ``retention_days``. Returns deleted count."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    result = await db.execute(
        delete(AuditEventModel).where(AuditEventModel.created_at < cutoff)
    )
    return result.rowcount  # type: ignore[return-value]
