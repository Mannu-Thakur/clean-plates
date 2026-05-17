"""Roles controller - thin dispatch layer."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserSchema
from app.schemas.roles import RoleSchema, RoleUpdateSchema
from app.services import roles_service


async def list_roles(db: AsyncSession) -> list[RoleSchema]:
    return await roles_service.list_roles(db)


async def update_role(
    db: AsyncSession,
    role_id: str,
    body: RoleUpdateSchema,
    *,
    current_user: UserSchema,
) -> RoleSchema:
    return await roles_service.update_role(db, role_id, body, current_user=current_user)
