"""Runtime configuration routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import config_controller
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.auth import UserSchema
from app.schemas.config import (
    BranchSchema,
    ConfigDataSchema,
    ConfigUpdateSchema,
    MealTimingSchema,
    SystemPolicySchema,
    ThresholdSchema,
)

router = APIRouter(prefix="/config", tags=["Configuration"])

CONFIG_READ_ROLES = ("super_admin", "institution_admin", "mess_admin")
CONFIG_WRITE_ROLES = ("super_admin", "institution_admin")


@router.get("/institution", response_model=ConfigDataSchema)
async def get_institution_config(
    current_user: UserSchema = Depends(require_roles(*CONFIG_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await config_controller.get_config(db, "institution")


@router.patch("/institution", response_model=ConfigDataSchema)
async def update_institution_config(
    body: ConfigUpdateSchema,
    current_user: UserSchema = Depends(require_roles(*CONFIG_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await config_controller.update_config(db, "institution", body, current_user=current_user)


@router.get("/device", response_model=ConfigDataSchema)
async def get_device_config(
    current_user: UserSchema = Depends(require_roles(*CONFIG_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await config_controller.get_config(db, "device")


@router.patch("/device", response_model=ConfigDataSchema)
async def update_device_config(
    body: ConfigUpdateSchema,
    current_user: UserSchema = Depends(require_roles(*CONFIG_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await config_controller.update_config(db, "device", body, current_user=current_user)


@router.get("/thresholds", response_model=ThresholdSchema)
async def get_thresholds(
    current_user: UserSchema = Depends(require_roles(*CONFIG_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await config_controller.get_thresholds(db)


@router.patch("/thresholds", response_model=ThresholdSchema)
async def update_thresholds(
    body: ThresholdSchema,
    current_user: UserSchema = Depends(require_roles(*CONFIG_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await config_controller.update_thresholds(db, body, current_user=current_user)


@router.get("/meals", response_model=list[MealTimingSchema])
async def get_meal_timings(
    current_user: UserSchema = Depends(require_roles(*CONFIG_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await config_controller.get_meal_timings(db)


@router.put("/meals", response_model=list[MealTimingSchema])
async def update_meal_timings(
    body: list[MealTimingSchema],
    current_user: UserSchema = Depends(require_roles(*CONFIG_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await config_controller.update_meal_timings(db, body, current_user=current_user)


@router.get("/branches", response_model=list[BranchSchema])
async def get_branches(
    current_user: UserSchema = Depends(require_roles(*CONFIG_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await config_controller.get_branches(db)


@router.put("/branches", response_model=list[BranchSchema])
async def update_branches(
    body: list[BranchSchema],
    current_user: UserSchema = Depends(require_roles(*CONFIG_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await config_controller.update_branches(db, body, current_user=current_user)


@router.get("/system", response_model=SystemPolicySchema)
async def get_system_policies(
    current_user: UserSchema = Depends(require_roles("super_admin", "institution_admin")),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await config_controller.get_system_policies(db)


@router.patch("/system", response_model=SystemPolicySchema)
async def update_system_policies(
    body: SystemPolicySchema,
    current_user: UserSchema = Depends(require_roles("super_admin")),
    db: AsyncSession = Depends(get_db_session),
):
    return await config_controller.update_system_policies(db, body, current_user=current_user)


@router.post("/reset/{section}", response_model=ConfigDataSchema)
async def reset_defaults(
    section: str,
    current_user: UserSchema = Depends(require_roles("super_admin")),
    db: AsyncSession = Depends(get_db_session),
):
    return await config_controller.reset_defaults(db, section, current_user=current_user)
