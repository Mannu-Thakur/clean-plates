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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config import ConfigModel

# ── Section defaults (used when DB has no rows yet) ──────────────────────────
_SECTION_DEFAULTS: dict[str, dict[str, Any]] = {
    "institution": {
        "name": "CleanPlates Institution",
        "code": "CP",
        "timezone": "Asia/Kolkata",
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
        "access_token_expiry_minutes": 60,
        "refresh_token_expiry_days": 7,
        "min_password_length": 8,
        "require_uppercase": True,
        "require_numbers": True,
        "max_login_attempts": 5,
        "lockout_duration_minutes": 15,
        "session_timeout_minutes": 120,
    },
}


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
