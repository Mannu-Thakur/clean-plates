"""Filter preset routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import filter_preset_controller
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.auth import UserSchema
from app.schemas.common import MessageSchema
from app.schemas.filter_presets import FilterPresetCreateSchema, FilterPresetSchema, FilterPresetUpdateSchema


router = APIRouter(prefix="/filters", tags=["Filter Presets"])

FILTER_PRESET_ROLES = ("super_admin", "institution_admin", "mess_admin", "analytics_viewer")


@router.get("/presets", response_model=list[FilterPresetSchema])
async def list_presets(
    current_user: UserSchema = Depends(require_roles(*FILTER_PRESET_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await filter_preset_controller.list_presets(db, current_user=current_user)


@router.post("/presets", response_model=FilterPresetSchema, status_code=201)
async def save_preset(
    body: FilterPresetCreateSchema,
    current_user: UserSchema = Depends(require_roles(*FILTER_PRESET_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await filter_preset_controller.save_preset(db, body, current_user=current_user)


@router.get("/presets/{preset_id}", response_model=FilterPresetSchema)
async def get_preset(
    preset_id: UUID,
    current_user: UserSchema = Depends(require_roles(*FILTER_PRESET_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await filter_preset_controller.get_preset(db, str(preset_id), current_user=current_user)


@router.patch("/presets/{preset_id}", response_model=FilterPresetSchema)
async def update_preset(
    preset_id: UUID,
    body: FilterPresetUpdateSchema,
    current_user: UserSchema = Depends(require_roles(*FILTER_PRESET_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await filter_preset_controller.update_preset(db, str(preset_id), body, current_user=current_user)


@router.delete("/presets/{preset_id}", response_model=MessageSchema)
async def delete_preset(
    preset_id: UUID,
    current_user: UserSchema = Depends(require_roles(*FILTER_PRESET_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    await filter_preset_controller.delete_preset(db, str(preset_id), current_user=current_user)
    return MessageSchema(message="Filter preset deleted")
