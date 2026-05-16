"""Analytics response schemas for Phase 5."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class KpiCardSchema(BaseModel):
    label: str
    value: float | int | str
    unit: str | None = None
    trend: float | None = None
    trend_direction: str | None = None


class OverviewKpisSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_waste_today_grams: float
    total_waste_week_grams: float
    total_waste_month_grams: float
    avg_daily_waste_grams: float
    waste_reduction_pct: float | None
    peak_waste_time: str | None
    total_active_students: int
    students_under_warning: int
    students_under_penalty: int
    active_devices: int
    offline_devices: int
    alerts_today: int
    rule_violations_today: int


class TrendPointSchema(BaseModel):
    label: str
    value: float


class TrendDataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: str
    data: list[TrendPointSchema]


class ComparisonDataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current_label: str
    previous_label: str
    current_data: list[TrendPointSchema]
    previous_data: list[TrendPointSchema]


class MealDistributionItemSchema(BaseModel):
    meal_type: str
    total_grams: float
    percentage: float


class DistributionDataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period: str
    data: list[MealDistributionItemSchema]


class FoodRankingItemSchema(BaseModel):
    food_name: str
    total_grams: float
    entry_count: int
    percentage: float


class FoodRankingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period: str
    data: list[FoodRankingItemSchema]


class StudentRankingItemSchema(BaseModel):
    rank: int
    student_id: UUID
    device_id: str
    name: str | None
    avg_waste_grams: float
    total_waste_grams: float
    violation_count: int
    status: str


class StudentRankingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period: str
    data: list[StudentRankingItemSchema]


class PeakDataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    peak_hour: int | None
    peak_meal: str | None
    peak_weekday: str | None
    peak_hour_grams: float | None
    heatmap_data: list[dict]


class ScoreDistributionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    excellent_count: int
    good_count: int
    average_count: int
    poor_count: int
    overall_avg: float


class ImprovementDataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: UUID
    device_id: str
    name: str | None
    current_avg_grams: float
    previous_avg_grams: float
    improvement_pct: float
    direction: str
