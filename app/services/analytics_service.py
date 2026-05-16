"""Analytics service for Phase 5 dashboard endpoints."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import DeviceModel
from app.models.rule import RuleExecutionModel
from app.models.student import StudentMappingModel, StudentModel
from app.models.warning import EscalationModel, PenaltyModel, WarningModel
from app.models.waste import WasteEntryModel
from app.schemas.analytics import (
    ComparisonDataSchema,
    DistributionDataSchema,
    FoodRankingItemSchema,
    FoodRankingSchema,
    ImprovementDataSchema,
    MealDistributionItemSchema,
    OverviewKpisSchema,
    PeakDataSchema,
    ScoreDistributionSchema,
    StudentRankingItemSchema,
    StudentRankingSchema,
    TrendDataSchema,
    TrendPointSchema,
)
from app.services import config_service


_VALID_PERIODS = {"today", "yesterday", "7d", "30d", "semester", "all", "custom"}
_FALLBACK_TIMEZONES = {
    "Asia/Kolkata": timezone(timedelta(hours=5, minutes=30)),
    "Asia/Calcutta": timezone(timedelta(hours=5, minutes=30)),
    "UTC": UTC,
}
_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@dataclass(frozen=True, slots=True)
class DateWindow:
    label: str
    start_date: date | None
    end_date: date | None


@dataclass(slots=True)
class EntryRow:
    entry: WasteEntryModel
    student: StudentModel
    mapping: StudentMappingModel | None


def _round(value: float | int | None, digits: int = 2) -> float:
    return round(float(value or 0.0), digits)


def _improvement_pct(previous: float, current: float) -> float | None:
    if previous <= 0:
        return None
    return round(((previous - current) / previous) * 100.0, 2)


def _direction(improvement_pct: float) -> str:
    if improvement_pct > 5:
        return "improving"
    if improvement_pct < -5:
        return "worsening"
    return "stable"


async def _institution_timezone(db: AsyncSession) -> tzinfo:
    config = await config_service.get_config(db, "institution")
    name = str(config.get("timezone") or "Asia/Kolkata")
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return _FALLBACK_TIMEZONES.get(name, UTC)


def _local_today(tz: tzinfo) -> date:
    return datetime.now(tz).date()


def _entry_local_datetime(entry: WasteEntryModel, tz: tzinfo) -> datetime:
    """Convert entry timestamp to local tz. Naive timestamps are assumed UTC."""
    if entry.timestamp.tzinfo is None:
        return entry.timestamp.replace(tzinfo=UTC).astimezone(tz)
    return entry.timestamp.astimezone(tz)


async def _window(
    db: AsyncSession,
    period: str = "30d",
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> DateWindow:
    tz = await _institution_timezone(db)
    today = _local_today(tz)

    if date_from or date_to:
        if date_from and date_to and date_from > date_to:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date_from must be before date_to")
        return DateWindow("custom", date_from, date_to)

    normalized = (period or "30d").strip().lower()
    if normalized not in _VALID_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period must be one of today, yesterday, 7d, 30d, semester, all",
        )
    if normalized == "today":
        return DateWindow(normalized, today, today)
    if normalized == "yesterday":
        yesterday = today - timedelta(days=1)
        return DateWindow(normalized, yesterday, yesterday)
    if normalized == "7d":
        return DateWindow(normalized, today - timedelta(days=6), today)
    if normalized == "30d":
        return DateWindow(normalized, today - timedelta(days=29), today)
    if normalized == "semester":
        return DateWindow(normalized, today - timedelta(days=180), today)
    return DateWindow(normalized, None, None)


def _previous_window(window: DateWindow) -> DateWindow | None:
    if window.start_date is None or window.end_date is None:
        return None
    days = (window.end_date - window.start_date).days + 1
    previous_end = window.start_date - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days - 1)
    return DateWindow(f"previous_{window.label}", previous_start, previous_end)


def _date_labels(window: DateWindow) -> list[date]:
    if window.start_date is None or window.end_date is None:
        return []
    days = (window.end_date - window.start_date).days + 1
    return [window.start_date + timedelta(days=offset) for offset in range(days)]


def _student_filters(
    stmt,
    *,
    branch: str | None = None,
    year: int | None = None,
    hostel: str | None = None,
    status_filter: str | None = None,
):
    if branch:
        stmt = stmt.where(StudentMappingModel.branch == branch.strip())
    if year is not None:
        stmt = stmt.where(StudentMappingModel.year == year)
    if hostel:
        stmt = stmt.where(StudentMappingModel.hostel == hostel.strip())
    if status_filter:
        stmt = stmt.where(StudentModel.status == status_filter.strip().lower())
    return stmt


def _entry_filters(
    stmt,
    window: DateWindow,
    *,
    student_id: str | None = None,
    device_id: str | None = None,
    branch: str | None = None,
    year: int | None = None,
    hostel: str | None = None,
    meal_type: str | None = None,
    status_filter: str | None = None,
):
    if window.start_date:
        stmt = stmt.where(WasteEntryModel.session_date >= window.start_date)
    if window.end_date:
        stmt = stmt.where(WasteEntryModel.session_date <= window.end_date)
    if student_id:
        stmt = stmt.where(WasteEntryModel.student_id == student_id)
    if device_id:
        stmt = stmt.where(or_(WasteEntryModel.device_id == device_id, StudentModel.device_id == device_id))
    if meal_type:
        stmt = stmt.where(WasteEntryModel.meal_type == meal_type.strip().lower())
    return _student_filters(stmt, branch=branch, year=year, hostel=hostel, status_filter=status_filter)


def _entry_has_food(entry: WasteEntryModel, food: str | None) -> bool:
    if not food:
        return True
    needle = food.strip().lower()
    for item in entry.food_items or []:
        if str(item.get("name") or "").strip().lower() == needle:
            return True
    return False


async def _load_entry_rows(
    db: AsyncSession,
    window: DateWindow,
    *,
    student_id: str | None = None,
    device_id: str | None = None,
    branch: str | None = None,
    year: int | None = None,
    hostel: str | None = None,
    meal_type: str | None = None,
    food: str | None = None,
    status_filter: str | None = None,
) -> list[EntryRow]:
    stmt = (
        select(WasteEntryModel, StudentModel, StudentMappingModel)
        .join(StudentModel, WasteEntryModel.student_id == StudentModel.id)
        .outerjoin(StudentMappingModel, StudentMappingModel.student_id == StudentModel.id)
    )
    stmt = _entry_filters(
        stmt,
        window,
        student_id=student_id,
        device_id=device_id,
        branch=branch,
        year=year,
        hostel=hostel,
        meal_type=meal_type,
        status_filter=status_filter,
    )
    stmt = stmt.order_by(WasteEntryModel.session_date.asc(), WasteEntryModel.timestamp.asc())
    result = await db.execute(stmt)
    rows = [EntryRow(entry=entry, student=student, mapping=mapping) for entry, student, mapping in result.all()]
    if food:
        rows = [row for row in rows if _entry_has_food(row.entry, food)]
    return rows


async def _student_count(
    db: AsyncSession,
    *,
    branch: str | None = None,
    year: int | None = None,
    hostel: str | None = None,
    status_filter: str | None = None,
    only_active: bool = True,
) -> int:
    stmt = select(func.count(StudentModel.id)).outerjoin(StudentMappingModel)
    if only_active:
        stmt = stmt.where(StudentModel.is_active.is_(True))
    stmt = _student_filters(stmt, branch=branch, year=year, hostel=hostel, status_filter=status_filter)
    return int((await db.execute(stmt)).scalar_one() or 0)


def _total(rows: list[EntryRow]) -> float:
    return sum(float(row.entry.weight_grams) for row in rows)


def _day_count(rows: list[EntryRow], window: DateWindow) -> int:
    if window.start_date and window.end_date:
        return max((window.end_date - window.start_date).days + 1, 1)
    days = {row.entry.session_date for row in rows}
    return max(len(days), 1)


def _food_item_totals(rows: list[EntryRow]) -> dict[str, tuple[float, set[str]]]:
    totals: dict[str, tuple[float, set[str]]] = {}
    for row in rows:
        items = row.entry.food_items or []
        names = [str(item.get("name") or "").strip() for item in items if str(item.get("name") or "").strip()]
        fallback_grams = float(row.entry.weight_grams) / len(names) if names else 0.0
        for item in items:
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            grams = item.get("grams")
            grams_value = float(grams) if grams is not None else fallback_grams
            current_total, entry_ids = totals.get(name, (0.0, set()))
            entry_ids.add(row.entry.id)
            totals[name] = (current_total + grams_value, entry_ids)
    return totals


async def _violation_counts(
    db: AsyncSession,
    student_ids: set[str],
    window: DateWindow,
) -> dict[str, int]:
    if not student_ids:
        return {}

    counts = {student_id: 0 for student_id in student_ids}
    warning_stmt = select(WarningModel.student_id, func.count(WarningModel.id)).where(
        WarningModel.student_id.in_(student_ids)
    )
    penalty_stmt = select(PenaltyModel.student_id, func.count(PenaltyModel.id)).where(
        PenaltyModel.student_id.in_(student_ids)
    )
    if window.start_date:
        warning_stmt = warning_stmt.where(func.date(WarningModel.created_at) >= window.start_date.isoformat())
        penalty_stmt = penalty_stmt.where(func.date(PenaltyModel.created_at) >= window.start_date.isoformat())
    if window.end_date:
        warning_stmt = warning_stmt.where(func.date(WarningModel.created_at) <= window.end_date.isoformat())
        penalty_stmt = penalty_stmt.where(func.date(PenaltyModel.created_at) <= window.end_date.isoformat())

    warning_result = await db.execute(warning_stmt.group_by(WarningModel.student_id))
    penalty_result = await db.execute(penalty_stmt.group_by(PenaltyModel.student_id))
    for student_id, count in warning_result.all():
        counts[str(student_id)] = counts.get(str(student_id), 0) + int(count or 0)
    for student_id, count in penalty_result.all():
        counts[str(student_id)] = counts.get(str(student_id), 0) + int(count or 0)
    return counts


async def get_overview(
    db: AsyncSession,
    *,
    period: str = "30d",
    date_from: date | None = None,
    date_to: date | None = None,
    student_id: str | None = None,
    device_id: str | None = None,
    branch: str | None = None,
    year: int | None = None,
    hostel: str | None = None,
    meal_type: str | None = None,
    food: str | None = None,
    status_filter: str | None = None,
) -> OverviewKpisSchema:
    tz = await _institution_timezone(db)
    today = _local_today(tz)
    selected_window = await _window(db, period, date_from=date_from, date_to=date_to)
    selected_rows = await _load_entry_rows(
        db,
        selected_window,
        student_id=student_id,
        device_id=device_id,
        branch=branch,
        year=year,
        hostel=hostel,
        meal_type=meal_type,
        food=food,
        status_filter=status_filter,
    )

    base_filters = {
        "student_id": student_id,
        "device_id": device_id,
        "branch": branch,
        "year": year,
        "hostel": hostel,
        "meal_type": meal_type,
        "food": food,
        "status_filter": status_filter,
    }
    today_rows = selected_rows if period == "today" else await _load_entry_rows(db, DateWindow("today", today, today), **base_filters)
    week_rows = selected_rows if period == "7d" else await _load_entry_rows(db, DateWindow("7d", today - timedelta(days=6), today), **base_filters)
    month_rows = selected_rows if period == "30d" else await _load_entry_rows(db, DateWindow("30d", today - timedelta(days=29), today), **base_filters)

    previous = _previous_window(selected_window)
    previous_total = None
    if previous is not None:
        previous_rows = await _load_entry_rows(db, previous, **base_filters)
        previous_total = _total(previous_rows)
    current_total = _total(selected_rows)
    reduction = _improvement_pct(previous_total or 0.0, current_total) if previous_total is not None else None

    peak_waste_time = None
    if selected_rows:
        by_hour: dict[int, float] = defaultdict(float)
        for row in selected_rows:
            by_hour[_entry_local_datetime(row.entry, tz).hour] += float(row.entry.weight_grams)
        peak_hour = max(by_hour.items(), key=lambda item: item[1])[0]
        peak_waste_time = f"{peak_hour:02d}:00"

    active_students = await _student_count(
        db,
        branch=branch,
        year=year,
        hostel=hostel,
        status_filter=status_filter,
        only_active=True,
    )
    warning_students_stmt = select(func.count(StudentModel.id)).outerjoin(StudentMappingModel).where(
        StudentModel.warning_count > 0,
        StudentModel.is_active.is_(True),
    )
    penalty_students_stmt = select(func.count(StudentModel.id)).outerjoin(StudentMappingModel).where(
        StudentModel.penalty_count > 0,
        StudentModel.is_active.is_(True),
    )
    warning_students_stmt = _student_filters(
        warning_students_stmt, branch=branch, year=year, hostel=hostel, status_filter=status_filter
    )
    penalty_students_stmt = _student_filters(
        penalty_students_stmt, branch=branch, year=year, hostel=hostel, status_filter=status_filter
    )

    active_devices = await db.scalar(
        select(func.count(DeviceModel.id)).where(DeviceModel.status == "online", DeviceModel.is_deleted.is_(False))
    )
    offline_devices = await db.scalar(
        select(func.count(DeviceModel.id)).where(DeviceModel.status == "offline", DeviceModel.is_deleted.is_(False))
    )

    alerts_today = int(
        (
            await db.execute(
                select(func.count(WarningModel.id)).where(func.date(WarningModel.created_at) == today.isoformat())
            )
        ).scalar_one()
        or 0
    )
    alerts_today += int(
        (
            await db.execute(
                select(func.count(PenaltyModel.id)).where(func.date(PenaltyModel.created_at) == today.isoformat())
            )
        ).scalar_one()
        or 0
    )
    alerts_today += int(
        (
            await db.execute(
                select(func.count(EscalationModel.id)).where(
                    EscalationModel.status == "pending",
                    func.date(EscalationModel.created_at) == today.isoformat(),
                )
            )
        ).scalar_one()
        or 0
    )
    rule_violations_today = int(
        (
            await db.execute(
                select(func.count(RuleExecutionModel.id)).where(
                    RuleExecutionModel.result_status.in_(("success", "partial")),
                    func.date(RuleExecutionModel.executed_at) == today.isoformat(),
                )
            )
        ).scalar_one()
        or 0
    )

    return OverviewKpisSchema(
        total_waste_today_grams=_round(_total(today_rows)),
        total_waste_week_grams=_round(_total(week_rows)),
        total_waste_month_grams=_round(_total(month_rows)),
        avg_daily_waste_grams=_round(current_total / _day_count(selected_rows, selected_window)),
        waste_reduction_pct=reduction,
        peak_waste_time=peak_waste_time,
        total_active_students=active_students,
        students_under_warning=int((await db.execute(warning_students_stmt)).scalar_one() or 0),
        students_under_penalty=int((await db.execute(penalty_students_stmt)).scalar_one() or 0),
        active_devices=int(active_devices or 0),
        offline_devices=int(offline_devices or 0),
        alerts_today=alerts_today,
        rule_violations_today=rule_violations_today,
    )


async def get_monthly_comparison(
    db: AsyncSession,
    *,
    student_id: str | None = None,
    device_id: str | None = None,
    branch: str | None = None,
    year: int | None = None,
    hostel: str | None = None,
    meal_type: str | None = None,
    food: str | None = None,
    status_filter: str | None = None,
) -> ComparisonDataSchema:
    tz = await _institution_timezone(db)
    today = _local_today(tz)
    current_start = today.replace(day=1)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end.replace(day=1)
    filters = {
        "student_id": student_id,
        "device_id": device_id,
        "branch": branch,
        "year": year,
        "hostel": hostel,
        "meal_type": meal_type,
        "food": food,
        "status_filter": status_filter,
    }
    current_window = DateWindow("current_month", current_start, today)
    previous_window = DateWindow("previous_month", previous_start, previous_end)
    current_rows = await _load_entry_rows(db, current_window, **filters)
    previous_rows = await _load_entry_rows(db, previous_window, **filters)

    def daily_points(rows: list[EntryRow], labels: list[date]) -> list[TrendPointSchema]:
        totals: dict[date, float] = defaultdict(float)
        for row in rows:
            totals[row.entry.session_date] += float(row.entry.weight_grams)
        return [TrendPointSchema(label=day.isoformat(), value=_round(totals.get(day, 0.0))) for day in labels]

    return ComparisonDataSchema(
        current_label=current_start.strftime("%B %Y"),
        previous_label=previous_start.strftime("%B %Y"),
        current_data=daily_points(current_rows, _date_labels(current_window)),
        previous_data=daily_points(previous_rows, _date_labels(previous_window)),
    )


async def get_trends(
    db: AsyncSession,
    *,
    trend_type: str = "weekly",
    period: str = "30d",
    date_from: date | None = None,
    date_to: date | None = None,
    student_id: str | None = None,
    device_id: str | None = None,
    branch: str | None = None,
    year: int | None = None,
    hostel: str | None = None,
    meal_type: str | None = None,
    food: str | None = None,
    status_filter: str | None = None,
) -> TrendDataSchema | ComparisonDataSchema:
    normalized_type = (trend_type or "weekly").strip().lower()
    filters = {
        "student_id": student_id,
        "device_id": device_id,
        "branch": branch,
        "year": year,
        "hostel": hostel,
        "meal_type": meal_type,
        "food": food,
        "status_filter": status_filter,
    }
    if normalized_type == "monthly_comparison":
        return await get_monthly_comparison(db, **filters)

    window = await _window(db, period, date_from=date_from, date_to=date_to)
    if normalized_type == "weekly" and not date_from and not date_to:
        tz = await _institution_timezone(db)
        today = _local_today(tz)
        window = DateWindow("7d", today - timedelta(days=6), today)
    elif normalized_type == "semester" and not date_from and not date_to:
        tz = await _institution_timezone(db)
        today = _local_today(tz)
        window = DateWindow("semester", today - timedelta(days=180), today)

    rows = await _load_entry_rows(db, window, **filters)
    if normalized_type == "semester":
        totals: dict[str, float] = defaultdict(float)
        for row in rows:
            totals[row.entry.session_date.strftime("%Y-%m")] += float(row.entry.weight_grams)
        data = [
            TrendPointSchema(label=label, value=_round(value))
            for label, value in sorted(totals.items(), key=lambda item: item[0])
        ]
        return TrendDataSchema(type=normalized_type, data=data)

    totals_by_date: dict[date, float] = defaultdict(float)
    for row in rows:
        totals_by_date[row.entry.session_date] += float(row.entry.weight_grams)
    labels = _date_labels(window) or sorted(totals_by_date)
    return TrendDataSchema(
        type=normalized_type,
        data=[TrendPointSchema(label=day.isoformat(), value=_round(totals_by_date.get(day, 0.0))) for day in labels],
    )


async def get_meal_distribution(
    db: AsyncSession,
    *,
    period: str = "30d",
    date_from: date | None = None,
    date_to: date | None = None,
    student_id: str | None = None,
    device_id: str | None = None,
    branch: str | None = None,
    year: int | None = None,
    hostel: str | None = None,
    meal_type: str | None = None,
    food: str | None = None,
    status_filter: str | None = None,
) -> DistributionDataSchema:
    window = await _window(db, period, date_from=date_from, date_to=date_to)
    rows = await _load_entry_rows(
        db,
        window,
        student_id=student_id,
        device_id=device_id,
        branch=branch,
        year=year,
        hostel=hostel,
        meal_type=meal_type,
        food=food,
        status_filter=status_filter,
    )
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        totals[row.entry.meal_type] += float(row.entry.weight_grams)
    grand_total = sum(totals.values())
    return DistributionDataSchema(
        period=window.label,
        data=[
            MealDistributionItemSchema(
                meal_type=meal,
                total_grams=_round(total),
                percentage=_round((total / grand_total) * 100.0) if grand_total else 0.0,
            )
            for meal, total in sorted(totals.items(), key=lambda item: item[1], reverse=True)
        ],
    )


async def get_food_waste_distribution(
    db: AsyncSession,
    *,
    period: str = "30d",
    date_from: date | None = None,
    date_to: date | None = None,
    student_id: str | None = None,
    device_id: str | None = None,
    branch: str | None = None,
    year: int | None = None,
    hostel: str | None = None,
    meal_type: str | None = None,
    food: str | None = None,
    status_filter: str | None = None,
    limit: int = 10,
) -> FoodRankingSchema:
    limit = min(max(limit, 1), 100)
    window = await _window(db, period, date_from=date_from, date_to=date_to)
    rows = await _load_entry_rows(
        db,
        window,
        student_id=student_id,
        device_id=device_id,
        branch=branch,
        year=year,
        hostel=hostel,
        meal_type=meal_type,
        food=food,
        status_filter=status_filter,
    )
    totals = _food_item_totals(rows)
    grand_total = sum(total for total, _ in totals.values())
    ranked = sorted(totals.items(), key=lambda item: item[1][0], reverse=True)[:limit]
    return FoodRankingSchema(
        period=window.label,
        data=[
            FoodRankingItemSchema(
                food_name=name,
                total_grams=_round(total),
                entry_count=len(entry_ids),
                percentage=_round((total / grand_total) * 100.0) if grand_total else 0.0,
            )
            for name, (total, entry_ids) in ranked
        ],
    )


async def get_top_contributors(
    db: AsyncSession,
    *,
    period: str = "30d",
    date_from: date | None = None,
    date_to: date | None = None,
    student_id: str | None = None,
    device_id: str | None = None,
    branch: str | None = None,
    year: int | None = None,
    hostel: str | None = None,
    meal_type: str | None = None,
    food: str | None = None,
    status_filter: str | None = None,
    limit: int = 10,
) -> StudentRankingSchema:
    limit = min(max(limit, 1), 100)
    window = await _window(db, period, date_from=date_from, date_to=date_to)
    rows = await _load_entry_rows(
        db,
        window,
        student_id=student_id,
        device_id=device_id,
        branch=branch,
        year=year,
        hostel=hostel,
        meal_type=meal_type,
        food=food,
        status_filter=status_filter,
    )
    grouped: dict[str, dict] = {}
    for row in rows:
        bucket = grouped.setdefault(
            row.student.id,
            {
                "student": row.student,
                "mapping": row.mapping,
                "total": 0.0,
                "count": 0,
            },
        )
        bucket["total"] += float(row.entry.weight_grams)
        bucket["count"] += 1

    violations = await _violation_counts(db, set(grouped), window)
    ranked = sorted(grouped.values(), key=lambda item: (item["total"], item["count"]), reverse=True)[:limit]
    return StudentRankingSchema(
        period=window.label,
        data=[
            StudentRankingItemSchema(
                rank=rank,
                student_id=item["student"].id,
                device_id=item["student"].device_id,
                name=item["mapping"].name if item["mapping"] else None,
                avg_waste_grams=_round(item["total"] / item["count"] if item["count"] else 0.0),
                total_waste_grams=_round(item["total"]),
                violation_count=violations.get(item["student"].id, 0),
                status=item["student"].status,
            )
            for rank, item in enumerate(ranked, start=1)
        ],
    )


async def get_improvement_tracking(
    db: AsyncSession,
    *,
    period: str = "30d",
    date_from: date | None = None,
    date_to: date | None = None,
    student_id: str | None = None,
    device_id: str | None = None,
    branch: str | None = None,
    year: int | None = None,
    hostel: str | None = None,
    meal_type: str | None = None,
    food: str | None = None,
    status_filter: str | None = None,
) -> list[ImprovementDataSchema]:
    window = await _window(db, period, date_from=date_from, date_to=date_to)
    if window.start_date is None or window.end_date is None:
        tz = await _institution_timezone(db)
        today = _local_today(tz)
        window = DateWindow("30d", today - timedelta(days=29), today)
    previous = _previous_window(window)
    filters = {
        "student_id": student_id,
        "device_id": device_id,
        "branch": branch,
        "year": year,
        "hostel": hostel,
        "meal_type": meal_type,
        "food": food,
        "status_filter": status_filter,
    }
    current_rows = await _load_entry_rows(db, window, **filters)
    previous_rows = await _load_entry_rows(db, previous, **filters) if previous else []

    def averages(rows: list[EntryRow]) -> dict[str, tuple[float, int, StudentModel, StudentMappingModel | None]]:
        grouped: dict[str, tuple[float, int, StudentModel, StudentMappingModel | None]] = {}
        for row in rows:
            total, count, _, _ = grouped.get(row.student.id, (0.0, 0, row.student, row.mapping))
            grouped[row.student.id] = (total + float(row.entry.weight_grams), count + 1, row.student, row.mapping)
        return grouped

    current = averages(current_rows)
    previous_map = averages(previous_rows)
    student_ids = set(current) | set(previous_map)
    items: list[ImprovementDataSchema] = []
    for sid in student_ids:
        current_total, current_count, student, mapping = current.get(sid, (0.0, 0, None, None))
        previous_total, previous_count, previous_student, previous_mapping = previous_map.get(sid, (0.0, 0, None, None))
        student = student or previous_student
        mapping = mapping or previous_mapping
        if student is None:
            continue
        current_avg = current_total / current_count if current_count else 0.0
        previous_avg = previous_total / previous_count if previous_count else 0.0
        improvement = _improvement_pct(previous_avg, current_avg)
        if improvement is None:
            improvement = 0.0 if current_avg == 0 else -100.0
        items.append(
            ImprovementDataSchema(
                student_id=student.id,
                device_id=student.device_id,
                name=mapping.name if mapping else None,
                current_avg_grams=_round(current_avg),
                previous_avg_grams=_round(previous_avg),
                improvement_pct=_round(improvement),
                direction=_direction(improvement),
            )
        )
    return sorted(items, key=lambda item: item.improvement_pct, reverse=True)


async def get_peak_waste(
    db: AsyncSession,
    *,
    period: str = "30d",
    date_from: date | None = None,
    date_to: date | None = None,
    student_id: str | None = None,
    device_id: str | None = None,
    branch: str | None = None,
    year: int | None = None,
    hostel: str | None = None,
    meal_type: str | None = None,
    food: str | None = None,
    status_filter: str | None = None,
) -> PeakDataSchema:
    tz = await _institution_timezone(db)
    window = await _window(db, period, date_from=date_from, date_to=date_to)
    rows = await _load_entry_rows(
        db,
        window,
        student_id=student_id,
        device_id=device_id,
        branch=branch,
        year=year,
        hostel=hostel,
        meal_type=meal_type,
        food=food,
        status_filter=status_filter,
    )
    hour_totals: dict[int, float] = defaultdict(float)
    meal_totals: dict[str, float] = defaultdict(float)
    weekday_totals: dict[str, float] = defaultdict(float)
    heatmap: dict[tuple[str, int], list[float | int]] = defaultdict(lambda: [0.0, 0])
    for row in rows:
        local_dt = _entry_local_datetime(row.entry, tz)
        weekday = _WEEKDAYS[local_dt.weekday()]
        hour = local_dt.hour
        grams = float(row.entry.weight_grams)
        hour_totals[hour] += grams
        meal_totals[row.entry.meal_type] += grams
        weekday_totals[weekday] += grams
        bucket = heatmap[(weekday, hour)]
        bucket[0] = float(bucket[0]) + grams
        bucket[1] = int(bucket[1]) + 1

    peak_hour, peak_hour_grams = (None, None)
    if hour_totals:
        peak_hour, peak_hour_grams = max(hour_totals.items(), key=lambda item: item[1])

    heatmap_data = [
        {
            "weekday": weekday,
            "hour": hour,
            "avg_grams": _round(float(total) / int(count) if count else 0.0),
        }
        for (weekday, hour), (total, count) in sorted(
            heatmap.items(), key=lambda item: (_WEEKDAYS.index(item[0][0]), item[0][1])
        )
    ]
    return PeakDataSchema(
        peak_hour=peak_hour,
        peak_meal=max(meal_totals.items(), key=lambda item: item[1])[0] if meal_totals else None,
        peak_weekday=max(weekday_totals.items(), key=lambda item: item[1])[0] if weekday_totals else None,
        peak_hour_grams=_round(peak_hour_grams) if peak_hour_grams is not None else None,
        heatmap_data=heatmap_data,
    )


async def get_sustainability_scores(
    db: AsyncSession,
    *,
    branch: str | None = None,
    year: int | None = None,
    hostel: str | None = None,
    status_filter: str | None = None,
) -> ScoreDistributionSchema:
    stmt = select(StudentModel.sustainability_score).outerjoin(StudentMappingModel).where(
        StudentModel.is_active.is_(True)
    )
    stmt = _student_filters(stmt, branch=branch, year=year, hostel=hostel, status_filter=status_filter)
    result = await db.execute(stmt)
    scores = [float(score or 0.0) for score in result.scalars().all()]
    return ScoreDistributionSchema(
        excellent_count=sum(1 for score in scores if score >= 90),
        good_count=sum(1 for score in scores if 75 <= score < 90),
        average_count=sum(1 for score in scores if 50 <= score < 75),
        poor_count=sum(1 for score in scores if score < 50),
        overall_avg=_round(sum(scores) / len(scores) if scores else 0.0),
    )

