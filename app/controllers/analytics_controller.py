"""Analytics controller - thin dispatch layer over analytics_service."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

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
from app.services import analytics_service


async def get_overview(db: AsyncSession, **filters) -> OverviewKpisSchema:
    return await analytics_service.get_overview(db, **filters)


async def get_trends(db: AsyncSession, **filters) -> TrendDataSchema | ComparisonDataSchema:
    return await analytics_service.get_trends(db, **filters)


async def get_peak_waste(db: AsyncSession, **filters) -> PeakDataSchema:
    return await analytics_service.get_peak_waste(db, **filters)


async def get_meal_distribution(db: AsyncSession, **filters) -> DistributionDataSchema:
    return await analytics_service.get_meal_distribution(db, **filters)


async def get_food_waste_distribution(db: AsyncSession, **filters) -> FoodRankingSchema:
    return await analytics_service.get_food_waste_distribution(db, **filters)


async def get_top_contributors(db: AsyncSession, **filters) -> StudentRankingSchema:
    return await analytics_service.get_top_contributors(db, **filters)


async def get_improvement_tracking(db: AsyncSession, **filters) -> list[ImprovementDataSchema]:
    return await analytics_service.get_improvement_tracking(db, **filters)


async def get_sustainability_scores(
    db: AsyncSession,
    *,
    branch: str | None = None,
    year: int | None = None,
    hostel: str | None = None,
    status_filter: str | None = None,
) -> ScoreDistributionSchema:
    return await analytics_service.get_sustainability_scores(
        db,
        branch=branch,
        year=year,
        hostel=hostel,
        status_filter=status_filter,
    )
