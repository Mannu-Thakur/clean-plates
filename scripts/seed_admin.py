"""
Seed script — create a default super_admin user for initial login.

Usage: python scripts/seed_admin.py
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password


async def seed_admin() -> None:
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
        from app.models.user import UserModel

        result = await session.execute(
            select(UserModel).where(UserModel.email == "admin@cleanplates.dev")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("  [SKIP] Admin user already exists")
        else:
            hashed = await hash_password("Admin@123")
            session.add(UserModel(
                id=str(uuid.uuid4()),
                email="admin@cleanplates.dev",
                password_hash=hashed,
                name="System Admin",
                role="super_admin",
                is_active=True,
                failed_login_attempts=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ))
            print("  [OK] Created default admin: admin@cleanplates.local / Admin@123")

        await session.commit()

    await engine.dispose()
    print("\n[DONE] Admin seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed_admin())
