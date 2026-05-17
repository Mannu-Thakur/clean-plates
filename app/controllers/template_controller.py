"""Email template controller - thin dispatch layer."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserSchema
from app.schemas.templates import (
    EmailTemplateSchema,
    RenderedHtmlSchema,
    SampleDataSchema,
    TemplateCreateSchema,
    TemplateUpdateSchema,
)
from app.services import template_service


async def list_templates(db: AsyncSession, *, type_filter: str | None = None) -> list[EmailTemplateSchema]:
    return await template_service.list_templates(db, type_filter=type_filter)


async def create_template(
    db: AsyncSession,
    body: TemplateCreateSchema,
    *,
    current_user: UserSchema,
) -> EmailTemplateSchema:
    return await template_service.create_template(db, body, current_user=current_user)


async def get_template(db: AsyncSession, template_id: str) -> EmailTemplateSchema:
    return await template_service.get_template(db, template_id)


async def update_template(
    db: AsyncSession,
    template_id: str,
    body: TemplateUpdateSchema,
    *,
    current_user: UserSchema,
) -> EmailTemplateSchema:
    return await template_service.update_template(db, template_id, body, current_user=current_user)


async def delete_template(db: AsyncSession, template_id: str, *, current_user: UserSchema) -> None:
    await template_service.delete_template(db, template_id, current_user=current_user)


async def preview_template(db: AsyncSession, template_id: str, body: SampleDataSchema) -> RenderedHtmlSchema:
    return await template_service.preview_template(db, template_id, body)
