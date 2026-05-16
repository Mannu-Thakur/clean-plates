"""Filter preset controller - thin dispatch layer."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserSchema
from app.schemas.filter_presets import FilterPresetCreateSchema, FilterPresetSchema, FilterPresetUpdateSchema
from app.services import filter_preset_service


async def list_presets(db: AsyncSession, *, current_user: UserSchema) -> list[FilterPresetSchema]:
    return await filter_preset_service.list_presets(db, current_user=current_user)


async def save_preset(
    db: AsyncSession,
    body: FilterPresetCreateSchema,
    *,
    current_user: UserSchema,
) -> FilterPresetSchema:
    return await filter_preset_service.save_preset(db, body, current_user=current_user)


async def get_preset(db: AsyncSession, preset_id: str, *, current_user: UserSchema) -> FilterPresetSchema:
    return await filter_preset_service.get_preset(db, preset_id, current_user=current_user)


async def update_preset(
    db: AsyncSession,
    preset_id: str,
    body: FilterPresetUpdateSchema,
    *,
    current_user: UserSchema,
) -> FilterPresetSchema:
    return await filter_preset_service.update_preset(db, preset_id, body, current_user=current_user)


async def delete_preset(db: AsyncSession, preset_id: str, *, current_user: UserSchema) -> None:
    await filter_preset_service.delete_preset(db, preset_id, current_user=current_user)
