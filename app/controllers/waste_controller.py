"""
Waste controller - thin dispatch layer over waste_service.

Ref: docs/plans/02-controllers.md section 4.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.waste import (
    BulkWasteIngestSchema,
    PaginatedEntries,
    SessionSummarySchema,
    SyncResultSchema,
    WasteEntryCreateSchema,
    WasteEntryDetailSchema,
    WasteEntrySchema,
)
from app.services import waste_service


async def create_waste_entry(
    db: AsyncSession,
    body: WasteEntryCreateSchema,
) -> WasteEntrySchema:
    return await waste_service.create_waste_entry(db, body)


async def bulk_sync(db: AsyncSession, body: BulkWasteIngestSchema) -> SyncResultSchema:
    return await waste_service.bulk_sync(db, body)


async def get_entry(db: AsyncSession, entry_id: str) -> WasteEntryDetailSchema:
    return await waste_service.get_entry(db, entry_id)


async def list_entries(
    db: AsyncSession,
    *,
    student_id: str | None = None,
    device_id: str | None = None,
    meal_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedEntries:
    return await waste_service.list_entries(
        db,
        student_id=student_id,
        device_id=device_id,
        meal_type=meal_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        size=size,
    )


async def get_current_session(
    db: AsyncSession,
    *,
    device_id: str | None = None,
) -> SessionSummarySchema:
    return await waste_service.get_current_session(db, device_id=device_id)


async def get_recent_entries(
    db: AsyncSession,
    *,
    device_id: str | None = None,
    limit: int = 20,
) -> list[WasteEntrySchema]:
    return await waste_service.get_recent_entries(db, device_id=device_id, limit=limit)
