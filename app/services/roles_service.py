"""Role management service."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import RoleModel
from app.schemas.auth import UserSchema
from app.schemas.roles import RoleSchema, RoleUpdateSchema
from app.services import audit_service


def _audit_user(current_user: UserSchema | None) -> dict[str, str]:
    if current_user is None:
        return {}
    return {"user_id": current_user.id, "user_name": current_user.name, "user_role": current_user.role}


def _role_state(role: RoleModel) -> dict[str, Any]:
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "permissions": role.permissions,
        "is_system": role.is_system,
    }


def _validate_permissions(permissions: dict) -> dict[str, list[str]]:
    if not isinstance(permissions, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="permissions must be an object")
    normalized: dict[str, list[str]] = {}
    for resource, actions in permissions.items():
        if not isinstance(resource, str) or not resource.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="permission resource names must be strings")
        if not isinstance(actions, list) or not all(isinstance(action, str) for action in actions):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="permission actions must be string lists")
        clean_actions = sorted({action.strip().lower() for action in actions if action.strip()})
        unknown = set(clean_actions) - {"read", "write", "delete", "execute", "export"}
        if unknown:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported permission action(s): {', '.join(sorted(unknown))}",
            )
        normalized[resource.strip().lower()] = clean_actions
    return normalized


async def list_roles(db: AsyncSession) -> list[RoleSchema]:
    result = await db.execute(select(RoleModel).order_by(RoleModel.name.asc()))
    return [RoleSchema.model_validate(role) for role in result.scalars().all()]


async def update_role(
    db: AsyncSession,
    role_id: str,
    body: RoleUpdateSchema,
    *,
    current_user: UserSchema,
) -> RoleSchema:
    role = await db.get(RoleModel, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    before = _role_state(role)
    role.permissions = _validate_permissions(body.permissions)
    if body.description is not None:
        role.description = body.description.strip() or None
    await db.flush()
    await audit_service.log(
        db,
        event_type="role.updated",
        action="update",
        resource_type="role",
        resource_id=role.id,
        summary=f"Updated role '{role.name}'",
        before_state=before,
        after_state=_role_state(role),
        **_audit_user(current_user),
    )
    return RoleSchema.model_validate(role)
