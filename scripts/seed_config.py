"""
Seed script — populate ALL 8 config sections with system defaults.

⚠ M1-fix: Must populate all sections or Phase 3+ services will KeyError.

Run after: alembic upgrade head, seed_roles.py

Usage: python scripts/seed_config.py
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# ── All 8 config sections with defaults ──────────────────────────────────────
CONFIG_SECTIONS = {
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
        ],
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
        ],
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


async def seed_config() -> None:
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 15},
    )

    from sqlalchemy import event
    @event.listens_for(engine.sync_engine, "connect")
    def _set_pragmas(dbapi_conn, rec):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        from app.models.config import ConfigModel

        for section, data in CONFIG_SECTIONS.items():
            count = 0
            for key, value in data.items():
                result = await session.execute(
                    select(ConfigModel).where(
                        ConfigModel.section == section,
                        ConfigModel.key == key,
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    existing.value = value
                else:
                    session.add(ConfigModel(
                        id=str(uuid.uuid4()),
                        section=section,
                        key=key,
                        value=value,
                        updated_at=datetime.now(timezone.utc),
                    ))
                    count += 1

            print(f"  [OK] Section '{section}': {count} new keys, {len(data) - count} updated")

        await session.commit()

    await engine.dispose()
    print(f"\n[DONE] Config seeding complete -- all {len(CONFIG_SECTIONS)} sections populated.")


if __name__ == "__main__":
    asyncio.run(seed_config())
