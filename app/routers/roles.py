"""Role management routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import roles_controller
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.auth import UserSchema
from app.schemas.roles import RoleSchema, RoleUpdateSchema

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("/", response_model=list[RoleSchema])
async def list_roles(
    current_user: UserSchema = Depends(require_roles("super_admin", "institution_admin")),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await roles_controller.list_roles(db)


@router.patch("/{role_id}", response_model=RoleSchema)
async def update_role(
    role_id: UUID,
    body: RoleUpdateSchema,
    current_user: UserSchema = Depends(require_roles("super_admin")),
    db: AsyncSession = Depends(get_db_session),
):
    return await roles_controller.update_role(db, str(role_id), body, current_user=current_user)
