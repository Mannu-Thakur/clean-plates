"""Runtime config controller."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserSchema
from app.schemas.config import (
    AppearanceConfigSchema,
    BranchSchema,
    ConfigDataSchema,
    ConfigUpdateSchema,
    DeviceConfigSchema,
    MealTimingSchema,
    SecurityConfigSchema,
    SystemPolicySchema,
    ThresholdSchema,
)
from app.services import config_service


async def get_config(db: AsyncSession, section: str) -> ConfigDataSchema:
    return ConfigDataSchema(section=section, data=await config_service.get_config(db, section))


async def update_config(
    db: AsyncSession,
    section: str,
    body: ConfigUpdateSchema,
    *,
    current_user: UserSchema,
) -> ConfigDataSchema:
    return ConfigDataSchema(
        section=section,
        data=await config_service.update_config(db, section, body.data, current_user=current_user),
    )


async def reset_defaults(db: AsyncSession, section: str, *, current_user: UserSchema) -> ConfigDataSchema:
    return ConfigDataSchema(
        section=section,
        data=await config_service.reset_defaults(db, section, current_user=current_user),
    )


async def get_thresholds(db: AsyncSession) -> ThresholdSchema:
    return ThresholdSchema.model_validate(await config_service.get_config(db, "thresholds"))


async def update_thresholds(db: AsyncSession, body: ThresholdSchema, *, current_user: UserSchema) -> ThresholdSchema:
    data = await config_service.update_config(db, "thresholds", body.model_dump(), current_user=current_user)
    return ThresholdSchema.model_validate(data)


async def get_meal_timings(db: AsyncSession) -> list[MealTimingSchema]:
    return [MealTimingSchema.model_validate(item) for item in await config_service.get_meal_timings(db)]


async def update_meal_timings(
    db: AsyncSession,
    body: list[MealTimingSchema],
    *,
    current_user: UserSchema,
) -> list[MealTimingSchema]:
    items = await config_service.update_meal_timings(db, body, current_user=current_user)
    return [MealTimingSchema.model_validate(item) for item in items]


async def get_branches(db: AsyncSession) -> list[BranchSchema]:
    return [BranchSchema.model_validate(item) for item in await config_service.get_branches(db)]


async def update_branches(
    db: AsyncSession,
    body: list[BranchSchema],
    *,
    current_user: UserSchema,
) -> list[BranchSchema]:
    items = await config_service.update_branches(db, body, current_user=current_user)
    return [BranchSchema.model_validate(item) for item in items]


async def get_system_policies(db: AsyncSession) -> SystemPolicySchema:
    return SystemPolicySchema.model_validate(await config_service.get_config(db, "system"))


async def update_system_policies(
    db: AsyncSession,
    body: SystemPolicySchema,
    *,
    current_user: UserSchema,
) -> SystemPolicySchema:
    data = await config_service.update_config(db, "system", body.model_dump(), current_user=current_user)
    return SystemPolicySchema.model_validate(data)


async def get_device_config(db: AsyncSession) -> DeviceConfigSchema:
    return DeviceConfigSchema.model_validate(await config_service.get_config(db, "device"))


async def get_appearance(db: AsyncSession) -> AppearanceConfigSchema:
    return AppearanceConfigSchema.model_validate(await config_service.get_config(db, "appearance"))


async def get_security_config(db: AsyncSession) -> SecurityConfigSchema:
    return SecurityConfigSchema.model_validate(await config_service.get_config(db, "security"))
