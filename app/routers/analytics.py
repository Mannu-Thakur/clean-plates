"""Analytics router."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import analytics_controller
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
from app.schemas.analytics import (
    ComparisonDataSchema,
    DistributionDataSchema,
    FoodRankingSchema,
    ImprovementDataSchema,
    OverviewKpisSchema,
    PeakDataSchema,
    ScoreDistributionSchema,
    StudentRankingSchema,
    TrendDataSchema,
)
from app.schemas.auth import UserSchema


router = APIRouter(prefix="/analytics", tags=["Analytics"])

ANALYTICS_ROLES = ("super_admin", "institution_admin", "mess_admin", "analytics_viewer")


def analytics_filters(
    period: str = Query(default="30d"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    student_id: UUID | None = Query(default=None),
    device_id: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    year: int | None = Query(default=None, ge=1, le=4),
    hostel: str | None = Query(default=None),
    meal_type: str | None = Query(default=None),
    food: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
) -> dict[str, Any]:
    return {
        "period": period,
        "date_from": date_from,
        "date_to": date_to,
        "student_id": str(student_id) if student_id else None,
        "device_id": device_id,
        "branch": branch,
        "year": year,
        "hostel": hostel,
        "meal_type": meal_type,
        "food": food,
        "status_filter": status_filter,
    }


@router.get("/overview", response_model=OverviewKpisSchema)
async def get_overview(
    filters: dict[str, Any] = Depends(analytics_filters),
    current_user: UserSchema = Depends(require_roles(*ANALYTICS_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await analytics_controller.get_overview(db, **filters)


@router.get("/trends", response_model=TrendDataSchema | ComparisonDataSchema)
async def get_trends(
    trend_type: str = Query(default="weekly", alias="type"),
    filters: dict[str, Any] = Depends(analytics_filters),
    current_user: UserSchema = Depends(require_roles(*ANALYTICS_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await analytics_controller.get_trends(db, trend_type=trend_type, **filters)


@router.get("/peaks", response_model=PeakDataSchema)
async def get_peak_waste(
    filters: dict[str, Any] = Depends(analytics_filters),
    current_user: UserSchema = Depends(require_roles(*ANALYTICS_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await analytics_controller.get_peak_waste(db, **filters)


@router.get("/meal-distribution", response_model=DistributionDataSchema)
async def get_meal_distribution(
    filters: dict[str, Any] = Depends(analytics_filters),
    current_user: UserSchema = Depends(require_roles(*ANALYTICS_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await analytics_controller.get_meal_distribution(db, **filters)


@router.get("/food-waste-distribution", response_model=FoodRankingSchema)
async def get_food_waste_distribution(
    limit: int = Query(default=10, ge=1, le=100),
    filters: dict[str, Any] = Depends(analytics_filters),
    current_user: UserSchema = Depends(require_roles(*ANALYTICS_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await analytics_controller.get_food_waste_distribution(db, limit=limit, **filters)


@router.get("/top-waste-contributors", response_model=StudentRankingSchema)
async def get_top_contributors(
    limit: int = Query(default=10, ge=1, le=100),
    filters: dict[str, Any] = Depends(analytics_filters),
    current_user: UserSchema = Depends(require_roles(*ANALYTICS_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await analytics_controller.get_top_contributors(db, limit=limit, **filters)


@router.get("/improvement-tracking", response_model=list[ImprovementDataSchema])
async def get_improvement_tracking(
    filters: dict[str, Any] = Depends(analytics_filters),
    current_user: UserSchema = Depends(require_roles(*ANALYTICS_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await analytics_controller.get_improvement_tracking(db, **filters)


@router.get("/sustainability", response_model=ScoreDistributionSchema)
async def get_sustainability_scores(
    branch: str | None = Query(default=None),
    year: int | None = Query(default=None, ge=1, le=4),
    hostel: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: UserSchema = Depends(require_roles(*ANALYTICS_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await analytics_controller.get_sustainability_scores(
        db,
        branch=branch,
        year=year,
        hostel=hostel,
        status_filter=status_filter,
    )
