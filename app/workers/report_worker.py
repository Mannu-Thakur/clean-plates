"""ARQ task functions for Phase 6 reports, notifications, and email."""

from __future__ import annotations

from typing import Any

from app.services import email_service, notification_service, report_service


async def generate_report_task(ctx: dict[str, Any], report_id: str) -> None:
    db_session_factory = ctx["db_session_factory"]
    async with db_session_factory() as db:
        try:
            await report_service.generate_report_file(db, report_id)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def execute_scheduled_reports(ctx: dict[str, Any]) -> None:
    db_session_factory = ctx["db_session_factory"]
    arq_pool = ctx.get("redis")
    async with db_session_factory() as db:
        try:
            await report_service.execute_scheduled_reports(db, arq_pool=arq_pool)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def send_scheduled_notifications(ctx: dict[str, Any]) -> None:
    db_session_factory = ctx["db_session_factory"]
    arq_pool = ctx.get("redis")
    async with db_session_factory() as db:
        try:
            await notification_service.execute_scheduled_notifications(db, arq_pool=arq_pool)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def send_notification_task(ctx: dict[str, Any], notification_id: str) -> None:
    db_session_factory = ctx["db_session_factory"]
    async with db_session_factory() as db:
        try:
            await notification_service.dispatch_notification(db, notification_id)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def send_email_task(
    ctx: dict[str, Any],
    to: str | None = None,
    subject: str | None = None,
    body_html: str | None = None,
    template_id: str | None = None,
    context_data: dict[str, Any] | None = None,
    notification_id: str | None = None,
) -> dict[str, Any]:
    """Immediate email dispatch task used by auth, rules, and notifications.

    If ``notification_id`` is supplied, the full notification delivery pipeline
    runs so status and per-recipient rows are updated. Otherwise this sends a
    one-off email and returns a compact result dictionary for ARQ logs.
    """
    db_session_factory = ctx["db_session_factory"]
    async with db_session_factory() as db:
        try:
            if notification_id:
                await notification_service.dispatch_notification(db, notification_id)
                await db.commit()
                return {"success": True, "notification_id": notification_id}

            if template_id:
                rendered = await email_service.render_template(db, template_id, context_data or {})
                subject = rendered["subject"]
                body_html = rendered["body_html"]

            result = await email_service.send_email(to or "", subject or "", body_html or "")
            await db.commit()
            return {"success": result.success, "status": result.status, "error": result.error}
        except Exception:
            await db.rollback()
            raise
