"""Email template routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import template_controller
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.auth import UserSchema
from app.schemas.common import MessageSchema
from app.schemas.templates import (
    EmailTemplateSchema,
    RenderedHtmlSchema,
    SampleDataSchema,
    TemplateCreateSchema,
    TemplateUpdateSchema,
)

router = APIRouter(prefix="/templates", tags=["Email Templates"])

TEMPLATE_READ_ROLES = ("super_admin", "institution_admin", "mess_admin")
TEMPLATE_ADMIN_ROLES = ("super_admin", "institution_admin")


@router.get("/", response_model=list[EmailTemplateSchema])
async def list_templates(
    type_filter: str | None = Query(default=None, alias="type"),
    current_user: UserSchema = Depends(require_roles(*TEMPLATE_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await template_controller.list_templates(db, type_filter=type_filter)


@router.post("/", response_model=EmailTemplateSchema, status_code=201)
async def create_template(
    body: TemplateCreateSchema,
    current_user: UserSchema = Depends(require_roles(*TEMPLATE_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await template_controller.create_template(db, body, current_user=current_user)


@router.get("/{template_id}", response_model=EmailTemplateSchema)
async def get_template(
    template_id: UUID,
    current_user: UserSchema = Depends(require_roles(*TEMPLATE_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await template_controller.get_template(db, str(template_id))


@router.patch("/{template_id}", response_model=EmailTemplateSchema)
async def update_template(
    template_id: UUID,
    body: TemplateUpdateSchema,
    current_user: UserSchema = Depends(require_roles(*TEMPLATE_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await template_controller.update_template(db, str(template_id), body, current_user=current_user)


@router.delete("/{template_id}", response_model=MessageSchema)
async def delete_template(
    template_id: UUID,
    current_user: UserSchema = Depends(require_roles(*TEMPLATE_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    await template_controller.delete_template(db, str(template_id), current_user=current_user)
    return MessageSchema(message="Template deleted")


@router.post("/{template_id}/preview", response_model=RenderedHtmlSchema)
async def preview_template(
    template_id: UUID,
    body: SampleDataSchema,
    current_user: UserSchema = Depends(require_roles(*TEMPLATE_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await template_controller.preview_template(db, str(template_id), body)
