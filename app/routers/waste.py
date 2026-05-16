"""
Waste entry router.

Ref: docs/plans/03-routes.md section 4.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import waste_controller
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.auth import UserSchema
from app.schemas.waste import PaginatedEntries, SessionSummarySchema, WasteEntryDetailSchema, WasteEntrySchema

router = APIRouter(prefix="/waste", tags=["Waste"])

WASTE_READ_ROLES = ("super_admin", "institution_admin", "mess_admin", "analytics_viewer")
WASTE_LIVE_ROLES = ("super_admin", "institution_admin", "mess_admin", "analytics_viewer", "staff_operator")


@router.get("/entries", response_model=PaginatedEntries)
async def list_entries(
    student_id: UUID | None = Query(default=None),
    device_id: UUID | None = Query(default=None),
    meal_type: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: UserSchema = Depends(require_roles(*WASTE_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await waste_controller.list_entries(
        db,
        student_id=str(student_id) if student_id else None,
        device_id=str(device_id) if device_id else None,
        meal_type=meal_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        size=size,
    )


@router.get("/entries/{entry_id}", response_model=WasteEntryDetailSchema)
async def get_entry(
    entry_id: UUID,
    current_user: UserSchema = Depends(require_roles(*WASTE_READ_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await waste_controller.get_entry(db, str(entry_id))


@router.get("/current-session", response_model=SessionSummarySchema)
async def get_current_session(
    device_id: UUID | None = Query(default=None),
    current_user: UserSchema = Depends(require_roles(*WASTE_LIVE_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await waste_controller.get_current_session(db, device_id=str(device_id) if device_id else None)


@router.get("/recent", response_model=list[WasteEntrySchema])
async def get_recent_entries(
    device_id: UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: UserSchema = Depends(require_roles(*WASTE_LIVE_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await waste_controller.get_recent_entries(db, device_id=str(device_id) if device_id else None, limit=limit)
