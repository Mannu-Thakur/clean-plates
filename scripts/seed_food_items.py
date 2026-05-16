"""
Seed script - insert common food items for Phase 2.

Run after: alembic upgrade head

Usage: python scripts/seed_food_items.py
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


FOOD_ITEMS = [
    {"name": "rice", "category": "main"},
    {"name": "dal", "category": "main"},
    {"name": "sabzi", "category": "side"},
    {"name": "roti", "category": "main"},
    {"name": "salad", "category": "side"},
    {"name": "dessert", "category": "dessert"},
    {"name": "beverage", "category": "beverage"},
]


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def seed_food_items() -> None:
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 15},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _set_pragmas(dbapi_conn, rec):  # noqa: ARG001
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        from app.models.food import FoodItemModel

        created = 0
        updated = 0
        for item in FOOD_ITEMS:
            result = await session.execute(
                select(FoodItemModel).where(FoodItemModel.name == item["name"])
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.category = item["category"]
                existing.is_active = True
                updated += 1
            else:
                session.add(
                    FoodItemModel(
                        name=item["name"],
                        category=item["category"],
                        is_active=True,
                        created_at=_utcnow(),
                    )
                )
                created += 1

        await session.commit()

    await engine.dispose()
    print(f"[DONE] Food item seed complete - {created} created, {updated} updated.")


if __name__ == "__main__":
    asyncio.run(seed_food_items())
