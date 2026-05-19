"""
Config service — internal config management.

Created in Phase 1 for internal use by other services (e.g. waste_service
reads meal timings, aggregation_service reads timezone). The config HTTP
routes are NOT registered until Phase 6.

⚠ N1: If no rows exist for a section (before seed_config.py runs), returns
hardcoded schema defaults — never raises 404 or returns empty.

Ref: 02-controllers.md §11
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config import ConfigModel
from app.schemas.auth import UserSchema
from app.schemas.config import (
    AppearanceConfigSchema,
    BranchSchema,
    DeviceConfigSchema,
    InstitutionConfigSchema,
    MealTimingSchema,
    SecurityConfigSchema,
    SystemPolicySchema,
    ThresholdSchema,
)
from app.services import audit_service

# ── Section defaults (used when DB has no rows yet) ──────────────────────────
_SECTION_DEFAULTS: dict[str, dict[str, Any]] = {
    "institution": {
        "name": "CleanPlates Institution",
        "code": "CP",
        "timezone": "Asia/Kolkata",
        "address": None,
        "phone": None,
        "email": None,
        "website": None,
    },
    "thresholds": {
        "waste_threshold_grams": 150.0,
        "warning_threshold_grams": 100.0,
        "penalty_threshold_grams": 200.0,
        "improvement_target_pct": 25.0,
        "reset_duration_days": 30,
        "warning_count_for_penalty": 5,
    },
    "meals": {
        "timings": [
            {"name": "breakfast", "display_name": "Breakfast", "start_time": "07:00", "end_time": "09:30", "is_active": True, "order_index": 0},
            {"name": "lunch", "display_name": "Lunch", "start_time": "12:00", "end_time": "14:30", "is_active": True, "order_index": 1},
            {"name": "dinner", "display_name": "Dinner", "start_time": "19:00", "end_time": "21:30", "is_active": True, "order_index": 2},
        ]
    },
    "system": {
        "sync_frequency_minutes": 5,
        "offline_handling": "queue",
        "backup_interval_hours": 24,
        "data_retention_days": 365,
        "log_retention_days": 30,
        "audit_retention_days": 90,
    },
    "device": {
        "device_offline_threshold_minutes": 10,
        "heartbeat_interval_seconds": 60,
        "sync_batch_size": 100,
    },
    "appearance": {
        "theme": "dark",
        "logo_path": None,
        "primary_color": "#6366f1",
        "institution_display_name": None,
    },
    "branches": {
        "items": [
            {"code": "CSE", "name": "Computer Science & Engineering"},
            {"code": "ECE", "name": "Electronics & Communication"},
            {"code": "ME", "name": "Mechanical Engineering"},
            {"code": "CE", "name": "Civil Engineering"},
        ]
    },
    "security": {
        "access_token_expiry_minutes": 1440,
        "refresh_token_expiry_days": 30,
        "min_password_length": 8,
        "require_uppercase": True,
        "require_numbers": True,
        "max_login_attempts": 5,
        "lockout_duration_minutes": 15,
        "session_timeout_minutes": 1440,
    },
}

_SECTION_SCHEMAS = {
    "institution": InstitutionConfigSchema,
    "thresholds": ThresholdSchema,
    "system": SystemPolicySchema,
    "device": DeviceConfigSchema,
    "appearance": AppearanceConfigSchema,
    "security": SecurityConfigSchema,
}


def _audit_user(current_user: UserSchema | None) -> dict:
    if current_user is None:
        return {}
    return {"user_id": current_user.id, "user_name": current_user.name, "user_role": current_user.role}


def _validate_section(section: str, data: dict[str, Any]) -> dict[str, Any]:
    section = section.strip().lower()
    if section == "meals":
        timings = data.get("timings") if isinstance(data, dict) else data if isinstance(data, list) else None
        if not isinstance(timings, list):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="meals config requires a timings list")
        return {"timings": [MealTimingSchema.model_validate(item).model_dump() for item in timings]}
    if section == "branches":
        items = data.get("items") if isinstance(data, dict) else data if isinstance(data, list) else None
        if not isinstance(items, list):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="branches config requires an items list")
        return {"items": [BranchSchema.model_validate(item).model_dump() for item in items]}
    schema = _SECTION_SCHEMAS.get(section)
    if schema is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown config section '{section}'")
    return schema.model_validate(data).model_dump()


async def get_config(db: AsyncSession, section: str) -> dict[str, Any]:
    """Retrieve all key-value pairs for a config section.

    Returns hardcoded defaults if the section has no DB rows.
    """
    result = await db.execute(
        select(ConfigModel).where(ConfigModel.section == section)
    )
    rows = result.scalars().all()

    if not rows:
        return _SECTION_DEFAULTS.get(section, {})

    return {row.key: row.value for row in rows}


async def set_config(
    db: AsyncSession,
    section: str,
    data: dict[str, Any],
    updated_by: str | None = None,
) -> None:
    """Upsert config keys for a section."""
    for key, value in data.items():
        result = await db.execute(
            select(ConfigModel).where(
                ConfigModel.section == section,
                ConfigModel.key == key,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.value = value
            existing.updated_by = updated_by
        else:
            db.add(ConfigModel(
                section=section,
                key=key,
                value=value,
                updated_by=updated_by,
            ))

    await db.flush()


async def reset_section(db: AsyncSession, section: str, updated_by: str | None = None) -> dict[str, Any]:
    """Reset a config section to hardcoded defaults."""
    defaults = _SECTION_DEFAULTS.get(section, {})
    await set_config(db, section, defaults, updated_by=updated_by)
    return defaults


async def update_config(
    db: AsyncSession,
    section: str,
    data: dict[str, Any],
    *,
    current_user: UserSchema,
) -> dict[str, Any]:
    """Validate and update a config section, then audit the change."""
    section = section.strip().lower()
    before = await get_config(db, section)
    validated = _validate_section(section, data)
    await set_config(db, section, validated, updated_by=current_user.id)
    after = await get_config(db, section)
    await audit_service.log(
        db,
        event_type="config.updated",
        action="update",
        resource_type="config",
        resource_id=section,
        summary=f"Updated {section} configuration",
        before_state=before,
        after_state=after,
        **_audit_user(current_user),
    )
    return after


async def reset_defaults(db: AsyncSession, section: str, *, current_user: UserSchema) -> dict[str, Any]:
    section = section.strip().lower()
    if section not in _SECTION_DEFAULTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown config section '{section}'")
    before = await get_config(db, section)
    defaults = await reset_section(db, section, updated_by=current_user.id)
    await audit_service.log(
        db,
        event_type="config.reset",
        action="reset",
        resource_type="config",
        resource_id=section,
        summary=f"Reset {section} configuration to defaults",
        before_state=before,
        after_state=defaults,
        **_audit_user(current_user),
    )
    return defaults


async def get_meal_timings(db: AsyncSession) -> list[dict[str, Any]]:
    config = await get_config(db, "meals")
    return list(config.get("timings") or [])


async def update_meal_timings(
    db: AsyncSession,
    timings: list[MealTimingSchema],
    *,
    current_user: UserSchema,
) -> list[dict[str, Any]]:
    data = {"timings": [item.model_dump() for item in timings]}
    await update_config(db, "meals", data, current_user=current_user)
    return data["timings"]


async def get_branches(db: AsyncSession) -> list[dict[str, Any]]:
    config = await get_config(db, "branches")
    return list(config.get("items") or [])


async def update_branches(
    db: AsyncSession,
    branches: list[BranchSchema],
    *,
    current_user: UserSchema,
) -> list[dict[str, Any]]:
    data = {"items": [item.model_dump() for item in branches]}
    await update_config(db, "branches", data, current_user=current_user)
    return data["items"]
