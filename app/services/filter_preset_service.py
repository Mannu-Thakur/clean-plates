"""Service functions for saved analytics filter presets."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.filter_preset import FilterPresetModel
from app.schemas.auth import UserSchema
from app.schemas.filter_presets import FilterPresetCreateSchema, FilterPresetSchema, FilterPresetUpdateSchema
from app.services import audit_service


def _audit_user(current_user: UserSchema) -> dict:
    return {
        "user_id": str(current_user.id),
        "user_name": current_user.name,
        "user_role": current_user.role,
    }


def _preset_state(preset: FilterPresetModel) -> dict:
    return {
        "id": preset.id,
        "user_id": preset.user_id,
        "name": preset.name,
        "filter_state": preset.filter_state,
    }


async def _get_preset_or_404(db: AsyncSession, preset_id: str) -> FilterPresetModel:
    preset = await db.get(FilterPresetModel, preset_id)
    if preset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filter preset not found")
    return preset


def _ensure_owner(preset: FilterPresetModel, current_user: UserSchema) -> None:
    if preset.user_id != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Filter preset belongs to another user")


async def list_presets(db: AsyncSession, *, current_user: UserSchema) -> list[FilterPresetSchema]:
    result = await db.execute(
        select(FilterPresetModel)
        .where(FilterPresetModel.user_id == str(current_user.id))
        .order_by(FilterPresetModel.created_at.desc(), FilterPresetModel.name.asc())
    )
    return [FilterPresetSchema.model_validate(preset) for preset in result.scalars().all()]


async def save_preset(
    db: AsyncSession,
    body: FilterPresetCreateSchema,
    *,
    current_user: UserSchema,
) -> FilterPresetSchema:
    preset = FilterPresetModel(
        user_id=str(current_user.id),
        name=body.name,
        filter_state=body.filter_state,
    )
    db.add(preset)
    await db.flush()
    await audit_service.log(
        db,
        event_type="filter_preset.created",
        action="create",
        resource_type="filter_preset",
        resource_id=preset.id,
        summary=f"Saved filter preset '{preset.name}'",
        after_state=_preset_state(preset),
        **_audit_user(current_user),
    )
    return FilterPresetSchema.model_validate(preset)


async def get_preset(db: AsyncSession, preset_id: str, *, current_user: UserSchema) -> FilterPresetSchema:
    preset = await _get_preset_or_404(db, preset_id)
    _ensure_owner(preset, current_user)
    return FilterPresetSchema.model_validate(preset)


async def update_preset(
    db: AsyncSession,
    preset_id: str,
    body: FilterPresetUpdateSchema,
    *,
    current_user: UserSchema,
) -> FilterPresetSchema:
    preset = await _get_preset_or_404(db, preset_id)
    _ensure_owner(preset, current_user)
    data = body.model_dump(exclude_unset=True)
    if not data:
        return FilterPresetSchema.model_validate(preset)
    if data.get("name") is None and "name" in data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name cannot be null")
    if data.get("filter_state") is None and "filter_state" in data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="filter_state cannot be null")

    before = _preset_state(preset)
    for field, value in data.items():
        setattr(preset, field, value)
    await db.flush()
    await audit_service.log(
        db,
        event_type="filter_preset.updated",
        action="update",
        resource_type="filter_preset",
        resource_id=preset.id,
        summary=f"Updated filter preset '{preset.name}'",
        before_state=before,
        after_state=_preset_state(preset),
        **_audit_user(current_user),
    )
    return FilterPresetSchema.model_validate(preset)


async def delete_preset(db: AsyncSession, preset_id: str, *, current_user: UserSchema) -> None:
    preset = await _get_preset_or_404(db, preset_id)
    _ensure_owner(preset, current_user)
    before = _preset_state(preset)
    await db.delete(preset)
    await audit_service.log(
        db,
        event_type="filter_preset.deleted",
        action="delete",
        resource_type="filter_preset",
        resource_id=preset_id,
        summary=f"Deleted filter preset '{before['name']}'",
        before_state=before,
        **_audit_user(current_user),
    )
