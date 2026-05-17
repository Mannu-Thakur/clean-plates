"""Email template CRUD and rendering service."""

from __future__ import annotations

import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import EmailTemplateModel
from app.schemas.auth import UserSchema
from app.schemas.templates import (
    EmailTemplateSchema,
    RenderedHtmlSchema,
    SampleDataSchema,
    TemplateCreateSchema,
    TemplateUpdateSchema,
)
from app.services import audit_service, email_service


def _audit_user(current_user: UserSchema) -> dict:
    return {"user_id": current_user.id, "user_name": current_user.name, "user_role": current_user.role}


def extract_variables(*templates: str) -> list[str]:
    variables: set[str] = set()
    try:
        from jinja2 import Environment, meta
    except Exception:
        for template in templates:
            variables.update(re.findall(r"{{\s*([a-zA-Z_][\w.]*)\s*}}", template or ""))
        return sorted(variables)

    env = Environment(autoescape=True)
    for template in templates:
        parsed = env.parse(template or "")
        variables.update(meta.find_undeclared_variables(parsed))
    return sorted(variables)


def _state(template: EmailTemplateModel) -> dict:
    return {
        "id": template.id,
        "name": template.name,
        "type": template.type,
        "subject": template.subject,
        "variables": template.variables,
        "is_default": template.is_default,
    }


async def list_templates(db: AsyncSession, *, type_filter: str | None = None) -> list[EmailTemplateSchema]:
    stmt = select(EmailTemplateModel).where(EmailTemplateModel.is_deleted.is_(False))
    if type_filter:
        stmt = stmt.where(EmailTemplateModel.type == type_filter.strip().lower())
    stmt = stmt.order_by(EmailTemplateModel.is_default.desc(), EmailTemplateModel.type.asc(), EmailTemplateModel.name.asc())
    result = await db.execute(stmt)
    return [EmailTemplateSchema.model_validate(template) for template in result.scalars().all()]


async def get_template(db: AsyncSession, template_id: str) -> EmailTemplateSchema:
    template = await db.get(EmailTemplateModel, template_id)
    if template is None or template.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email template not found")
    return EmailTemplateSchema.model_validate(template)


async def create_template(db: AsyncSession, body: TemplateCreateSchema, *, current_user: UserSchema) -> EmailTemplateSchema:
    variables = sorted(set(body.variables) | set(extract_variables(body.subject, body.body_html)))
    template = EmailTemplateModel(
        name=body.name.strip(),
        type=body.type,
        subject=body.subject.strip(),
        body_html=body.body_html,
        variables=variables,
        is_default=False,
        created_by=current_user.id,
    )
    db.add(template)
    await db.flush()
    await audit_service.log(
        db,
        event_type="template.created",
        action="create",
        resource_type="template",
        resource_id=template.id,
        summary=f"Created email template '{template.name}'",
        after_state=_state(template),
        **_audit_user(current_user),
    )
    return EmailTemplateSchema.model_validate(template)


async def update_template(
    db: AsyncSession,
    template_id: str,
    body: TemplateUpdateSchema,
    *,
    current_user: UserSchema,
) -> EmailTemplateSchema:
    template = await db.get(EmailTemplateModel, template_id)
    if template is None or template.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email template not found")
    before = _state(template)
    update_data = body.model_dump(exclude_unset=True)
    for field in ("name", "subject", "body_html"):
        if field in update_data and update_data[field] is not None:
            setattr(template, field, update_data[field].strip() if isinstance(update_data[field], str) else update_data[field])
    if "variables" in update_data and update_data["variables"] is not None:
        explicit = set(update_data["variables"])
    else:
        explicit = set(template.variables or [])
    template.variables = sorted(explicit | set(extract_variables(template.subject, template.body_html)))
    await db.flush()
    await audit_service.log(
        db,
        event_type="template.updated",
        action="update",
        resource_type="template",
        resource_id=template.id,
        summary=f"Updated email template '{template.name}'",
        before_state=before,
        after_state=_state(template),
        **_audit_user(current_user),
    )
    return EmailTemplateSchema.model_validate(template)


async def delete_template(db: AsyncSession, template_id: str, *, current_user: UserSchema) -> None:
    template = await db.get(EmailTemplateModel, template_id)
    if template is None or template.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email template not found")
    if template.is_default:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Default templates cannot be deleted")
    before = _state(template)
    template.is_deleted = True
    await db.flush()
    await audit_service.log(
        db,
        event_type="template.deleted",
        action="delete",
        resource_type="template",
        resource_id=template.id,
        summary=f"Deleted email template '{template.name}'",
        before_state=before,
        **_audit_user(current_user),
    )


async def preview_template(db: AsyncSession, template_id: str, body: SampleDataSchema) -> RenderedHtmlSchema:
    template = await db.get(EmailTemplateModel, template_id)
    if template is None or template.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email template not found")
    rendered = email_service.render_string(template.body_html, body.variables)
    return RenderedHtmlSchema(html=rendered)
