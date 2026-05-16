"""
Condition matching for the stateless rule engine.

The matcher accepts either Pydantic rule schemas or raw JSON dictionaries from
the database. Simple field comparisons are resolved from the event context;
frequency, aggregate, and trend checks query the database for the current
student.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.waste import WasteEntryModel
from app.services import config_service


_NUMERIC_OPERATORS = {"gt", "gte", "lt", "lte", "eq", "neq", "between"}
_STRING_OPERATORS = {"eq", "neq", "in", "not_in", "contains"}
_FIELD_ALIASES = {
    "waste_grams": ("waste_grams", "weight_grams"),
    "food_item": ("food_item", "food_items"),
    "student_status": ("student_status", "status"),
}


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return dict(value or {})


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        return list(value)
    return [value]


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC).replace(tzinfo=None) if value.tzinfo else value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        return parsed.astimezone(UTC).replace(tzinfo=None) if parsed.tzinfo else parsed
    return _utcnow()


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _food_names(value: Any) -> list[str]:
    names: list[str] = []
    for item in _as_list(value):
        if isinstance(item, dict):
            name = item.get("name")
        else:
            name = item
        if name is not None:
            cleaned = str(name).strip()
            if cleaned:
                names.append(cleaned)
    return names


class ConditionMatcher:
    """Evaluate rule condition groups against an event context."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def match(self, condition_groups: list[Any], context: dict[str, Any]) -> bool:
        if not condition_groups:
            return True
        for group in condition_groups:
            if not await self._match_group(group, context):
                return False
        return True

    async def _match_group(self, group: Any, context: dict[str, Any]) -> bool:
        group_data = _as_dict(group)
        conditions = group_data.get("conditions") or []
        if not conditions:
            return True

        logic = str(group_data.get("logic") or "AND").upper()
        results = [await self._match_single(condition, context) for condition in conditions]
        if logic == "OR":
            return any(results)
        return all(results)

    async def _match_single(self, condition: Any, context: dict[str, Any]) -> bool:
        condition_data = _as_dict(condition)
        field = str(condition_data.get("field") or "").strip()
        operator = str(condition_data.get("operator") or "eq").strip().lower()
        expected = await self._resolve_expected_value(condition_data.get("value"))

        if field == "frequency_count":
            return await self._match_frequency(condition_data, context)
        if field in {"avg_waste_7d", "avg_waste_30d"}:
            days = 7 if field.endswith("7d") else 30
            return await self._match_aggregate(days, operator, expected, context)
        if field in {"trend", "waste_trend", "trend_7d"}:
            return await self._match_trend(condition_data, context)

        field_value = self._context_value(field, context)
        if isinstance(field_value, list):
            return self._match_list(operator, field_value, expected)

        numeric_left = _to_float(field_value)
        numeric_right = _to_float(expected)
        if operator in _NUMERIC_OPERATORS and numeric_left is not None:
            return self._match_numeric(operator, numeric_left, expected if operator == "between" else numeric_right)
        return self._match_string(operator, field_value, expected)

    async def _resolve_expected_value(self, value: Any) -> Any:
        if not isinstance(value, str):
            return value

        key = value.strip()
        prefixes = ("config.thresholds.", "thresholds.")
        for prefix in prefixes:
            if key.startswith(prefix):
                config_key = key[len(prefix) :]
                thresholds = await config_service.get_config(self.db, "thresholds")
                return thresholds.get(config_key)
        return value

    def _context_value(self, field: str, context: dict[str, Any]) -> Any:
        if field == "food_item":
            return _food_names(context.get("food_items"))
        for candidate in _FIELD_ALIASES.get(field, (field,)):
            if candidate in context:
                return context.get(candidate)
        return None

    def _match_list(self, operator: str, field_values: list[Any], expected: Any) -> bool:
        normalized_values = [str(value).lower() for value in field_values if value is not None]
        expected_values = [str(value).lower() for value in _as_list(expected)]
        if operator == "contains":
            return any(target in value for target in expected_values for value in normalized_values)
        if operator == "not_in":
            return all(value not in expected_values for value in normalized_values)
        if operator in {"in", "eq"}:
            return any(value in expected_values for value in normalized_values)
        if operator == "neq":
            return all(value not in expected_values for value in normalized_values)
        return False

    def _match_numeric(self, operator: str, field_value: float, threshold: Any) -> bool:
        if operator == "between":
            bounds = _as_list(threshold)
            if len(bounds) != 2:
                return False
            low = _to_float(bounds[0])
            high = _to_float(bounds[1])
            return low is not None and high is not None and low <= field_value <= high

        if threshold is None:
            return False
        threshold_value = float(threshold)
        if operator == "gt":
            return field_value > threshold_value
        if operator == "gte":
            return field_value >= threshold_value
        if operator == "lt":
            return field_value < threshold_value
        if operator == "lte":
            return field_value <= threshold_value
        if operator == "eq":
            return field_value == threshold_value
        if operator == "neq":
            return field_value != threshold_value
        return False

    def _match_string(self, operator: str, field_value: Any, target: Any) -> bool:
        if operator not in _STRING_OPERATORS:
            return False

        value = "" if field_value is None else str(field_value).lower()
        targets = [str(item).lower() for item in _as_list(target)]
        if operator == "eq":
            return value == (targets[0] if targets else "")
        if operator == "neq":
            return value != (targets[0] if targets else "")
        if operator == "in":
            return value in targets
        if operator == "not_in":
            return value not in targets
        if operator == "contains":
            return any(target_value in value for target_value in targets)
        return False

    async def _match_frequency(self, condition: dict[str, Any], context: dict[str, Any]) -> bool:
        student_id = context.get("student_id")
        if not student_id:
            return False

        value = condition.get("value")
        value_data = value if isinstance(value, dict) else {}
        threshold = _to_float(value_data.get("threshold", value))
        if threshold is None:
            return False

        operator = str(value_data.get("operator") or condition.get("operator") or "gte").lower()
        window_days = int(value_data.get("lookback_days") or value_data.get("window_days") or 7)
        timestamp = _parse_datetime(context.get("timestamp"))
        cutoff = timestamp - timedelta(days=max(window_days, 1))

        stmt = select(func.count(WasteEntryModel.id)).where(
            WasteEntryModel.student_id == str(student_id),
            WasteEntryModel.timestamp >= cutoff,
            WasteEntryModel.timestamp <= timestamp,
        )
        filters = value_data.get("filters") or {}
        if filters.get("meal_type"):
            stmt = stmt.where(WasteEntryModel.meal_type == str(filters["meal_type"]).lower())
        if filters.get("severity"):
            stmt = stmt.where(WasteEntryModel.severity == str(filters["severity"]).lower())
        if filters.get("min_grams") is not None:
            stmt = stmt.where(WasteEntryModel.weight_grams >= float(filters["min_grams"]))

        result = await self.db.execute(stmt)
        count = float(result.scalar_one() or 0)
        return self._match_numeric(operator, count, threshold)

    async def _match_aggregate(self, days: int, operator: str, expected: Any, context: dict[str, Any]) -> bool:
        student_id = context.get("student_id")
        threshold = _to_float(expected)
        if not student_id or threshold is None:
            return False

        timestamp = _parse_datetime(context.get("timestamp"))
        cutoff = timestamp - timedelta(days=days)
        result = await self.db.execute(
            select(func.avg(WasteEntryModel.weight_grams)).where(
                WasteEntryModel.student_id == str(student_id),
                WasteEntryModel.timestamp >= cutoff,
                WasteEntryModel.timestamp <= timestamp,
            )
        )
        average = float(result.scalar_one() or 0.0)
        return self._match_numeric(operator, average, threshold)

    async def _match_trend(self, condition: dict[str, Any], context: dict[str, Any]) -> bool:
        student_id = context.get("student_id")
        if not student_id:
            return False

        value = condition.get("value")
        value_data = value if isinstance(value, dict) else {"threshold": value}
        threshold = _to_float(value_data.get("threshold"))
        if threshold is None:
            return False

        operator = str(value_data.get("operator") or condition.get("operator") or "gte").lower()
        window_days = int(value_data.get("window_days") or 7)
        timestamp = _parse_datetime(context.get("timestamp"))
        current_start = timestamp - timedelta(days=window_days)
        previous_start = current_start - timedelta(days=window_days)

        async def _avg(start: datetime, end: datetime) -> float:
            result = await self.db.execute(
                select(func.avg(WasteEntryModel.weight_grams)).where(
                    WasteEntryModel.student_id == str(student_id),
                    WasteEntryModel.timestamp >= start,
                    WasteEntryModel.timestamp < end,
                )
            )
            return float(result.scalar_one() or 0.0)

        current_avg = await _avg(current_start, timestamp)
        previous_avg = await _avg(previous_start, current_start)
        if previous_avg <= 0:
            return False
        delta_pct = ((current_avg - previous_avg) / previous_avg) * 100.0
        return self._match_numeric(operator, delta_pct, threshold)
