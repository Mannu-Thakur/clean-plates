"""
Seed script — insert 5 default roles with is_system=True.

Permissions matrix from 01-models.md §23.
Run after: alembic upgrade head

Usage: python scripts/seed_roles.py
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# ── Permission matrix (source of truth: 01-models.md §23) ───────────────────
ROLE_PERMISSIONS = {
    "super_admin": {
        "description": "Full system access — all resources, all actions",
        "permissions": {
            "students": ["read", "write"],
            "waste": ["read", "write"],
            "warnings": ["read", "write"],
            "penalties": ["read", "write"],
            "escalations": ["read", "write"],
            "rules": ["read", "write"],
            "analytics": ["read"],
            "devices": ["read", "write"],
            "config": ["read", "write"],
            "notifications": ["read", "write"],
            "reports": ["read", "write"],
            "audit": ["read"],
            "settings": ["read", "write"],
            "roles": ["read", "write"],
        },
    },
    "institution_admin": {
        "description": "Institution-level admin — most resources, limited settings",
        "permissions": {
            "students": ["read", "write"],
            "waste": ["read", "write"],
            "warnings": ["read", "write"],
            "penalties": ["read", "write"],
            "escalations": ["read", "write"],
            "rules": ["read", "write"],
            "analytics": ["read"],
            "devices": ["read", "write"],
            "config": ["read", "write"],
            "notifications": ["read", "write"],
            "reports": ["read", "write"],
            "audit": ["read"],
            "settings": ["read"],
            "roles": ["read"],
        },
    },
    "mess_admin": {
        "description": "Mess-level admin — student management, warnings, no rules",
        "permissions": {
            "students": ["read", "write"],
            "waste": ["read", "write"],
            "warnings": ["read", "write"],
            "penalties": ["read"],
            "escalations": ["read"],
            "analytics": ["read"],
            "devices": ["read"],
            "config": ["read"],
            "notifications": ["read", "write"],
            "reports": ["read", "write"],
        },
    },
    "analytics_viewer": {
        "description": "Read-only analytics and student data",
        "permissions": {
            "students": ["read"],
            "waste": ["read"],
            "analytics": ["read"],
            "reports": ["read"],
        },
    },
    "staff_operator": {
        "description": "Day-to-day operator — waste entry, student lookup",
        "permissions": {
            "students": ["read"],
            "waste": ["read", "write"],
            "warnings": ["read"],
            "devices": ["read"],
        },
    },
}


async def seed_roles() -> None:
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 15},
    )

    # Enable FKs
    from sqlalchemy import event
    @event.listens_for(engine.sync_engine, "connect")
    def _set_pragmas(dbapi_conn, rec):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Import model here to avoid circular imports
        from app.models.role import RoleModel

        for role_name, role_data in ROLE_PERMISSIONS.items():
            result = await session.execute(
                select(RoleModel).where(RoleModel.name == role_name)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update permissions if role already exists
                existing.permissions = role_data["permissions"]
                existing.description = role_data["description"]
                existing.is_system = True
                print(f"  [UPD] Updated role: {role_name}")
            else:
                session.add(RoleModel(
                    id=str(uuid.uuid4()),
                    name=role_name,
                    description=role_data["description"],
                    permissions=role_data["permissions"],
                    is_system=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                ))
                print(f"  [OK] Created role: {role_name}")

        await session.commit()

    await engine.dispose()
    print("\n[DONE] Role seeding complete -- 5 system roles ready.")


if __name__ == "__main__":
    asyncio.run(seed_roles())
