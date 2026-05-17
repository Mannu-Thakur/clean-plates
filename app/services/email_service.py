"""Email rendering and dispatch service."""

from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.notification import EmailTemplateModel


@dataclass(slots=True)
class SendResult:
    success: bool
    status: str
    error: str | None = None
    skipped: bool = False


@dataclass(slots=True)
class BulkResult:
    total: int
    sent: int
    failed: int
    errors: list[dict[str, str]]


def render_string(template: str, context_data: dict[str, Any]) -> str:
    try:
        from jinja2 import Template
    except Exception:
        rendered = template
        for key, value in context_data.items():
            rendered = rendered.replace("{{ " + key + " }}", str(value)).replace("{{" + key + "}}", str(value))
        return rendered
    return Template(template).render(**context_data)


async def render_template(db: AsyncSession, template_id: str, context_data: dict[str, Any]) -> dict[str, str]:
    template = await db.get(EmailTemplateModel, template_id)
    if template is None or template.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email template not found")
    return {
        "subject": render_string(template.subject, context_data),
        "body_html": render_string(template.body_html, context_data),
    }


async def send_email(to: str, subject: str, body_html: str) -> SendResult:
    to = (to or "").strip()
    if not to:
        return SendResult(success=False, status="failed", error="Missing recipient email")

    if not settings.EMAIL_ENABLED:
        return SendResult(success=True, status="delivered", skipped=True)

    if not settings.SMTP_HOST:
        return SendResult(success=False, status="failed", error="SMTP_HOST is not configured")

    try:
        import aiosmtplib
    except Exception as exc:
        return SendResult(success=False, status="failed", error=f"aiosmtplib unavailable: {exc}")

    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content("This message requires an HTML-capable email client.")
    message.add_alternative(body_html, subtype="html")

    try:
        kwargs: dict[str, Any] = {
            "hostname": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "timeout": 15,
        }
        if settings.SMTP_USER:
            kwargs["username"] = settings.SMTP_USER
            kwargs["password"] = settings.SMTP_PASSWORD
        if settings.SMTP_PORT == 465:
            kwargs["use_tls"] = True
        else:
            kwargs["start_tls"] = True
        await aiosmtplib.send(message, **kwargs)
    except Exception as exc:
        return SendResult(success=False, status="failed", error=str(exc))

    return SendResult(success=True, status="delivered")


async def send_bulk(
    db: AsyncSession,
    recipients: list[dict[str, Any]],
    *,
    template_id: str | None = None,
    subject: str | None = None,
    body_html: str | None = None,
    context_data: dict[str, Any] | None = None,
) -> BulkResult:
    sent = 0
    failed = 0
    errors: list[dict[str, str]] = []
    for recipient in recipients:
        context = {**(context_data or {}), **recipient}
        if template_id:
            rendered = await render_template(db, template_id, context)
            item_subject = rendered["subject"]
            item_body = rendered["body_html"]
        else:
            item_subject = render_string(subject or "", context)
            item_body = render_string(body_html or "", context)
        result = await send_email(str(recipient.get("email") or ""), item_subject, item_body)
        if result.success:
            sent += 1
        else:
            failed += 1
            errors.append({"recipient": str(recipient.get("id") or recipient.get("email") or ""), "error": result.error or ""})
    return BulkResult(total=len(recipients), sent=sent, failed=failed, errors=errors)
