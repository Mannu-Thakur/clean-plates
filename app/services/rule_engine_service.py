"""Rule CRUD, testing, simulation, and event evaluation."""

from __future__ import annotations

import math
from datetime import UTC, date, datetime
from typing import Any

from arq.connections import ArqRedis
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.engine.action_executor import ActionExecutor, ActionResult
from app.engine.condition_matcher import ConditionMatcher
from app.models.rule import RuleExecutionModel, RuleModel
from app.models.student import StudentMappingModel, StudentModel
from app.models.waste import WasteEntryModel
from app.schemas.auth import UserSchema
from app.schemas.rules import (
    ActionOptionSchema,
    ChainDataSchema,
    ChainEdgeSchema,
    ChainNodeSchema,
    FieldOptionSchema,
    OperatorOptionSchema,
    PaginatedExecutions,
    PaginatedRules,
    RuleCreateSchema,
    RuleExecutionSchema,
    RuleSchema,
    RuleUpdateSchema,
    SimulationResultSchema,
    TestPayloadSchema,
    TestResultSchema,
)
from app.services import audit_service


_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_SORT_COLUMNS = {
    "name": RuleModel.name,
    "type": RuleModel.type,
    "priority": RuleModel.priority,
    "active": RuleModel.active,
    "execution_count": RuleModel.execution_count,
    "last_triggered_at": RuleModel.last_triggered_at,
    "created_at": RuleModel.created_at,
    "updated_at": RuleModel.updated_at,
}
_TRIGGER_ENTITY_KEYS = ("waste_entry_id", "entry_id", "warning_id", "penalty_id", "device_id")


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _dump(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_dump(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _dump(item) for key, item in value.items()}
    return value


def _audit_user(current_user: UserSchema | None) -> dict[str, Any]:
    if current_user is None:
        return {}
    return {
        "user_id": str(current_user.id),
        "user_name": current_user.name,
        "user_role": current_user.role,
    }


def _rule_state(rule: RuleModel) -> dict[str, Any]:
    return {
        "id": rule.id,
        "name": rule.name,
        "description": rule.description,
        "type": rule.type,
        "priority": rule.priority,
        "active": rule.active,
        "conditions": rule.conditions,
        "time_constraints": rule.time_constraints,
        "scope": rule.scope,
        "actions": rule.actions,
        "chain_to_rule_id": rule.chain_to_rule_id,
        "is_deleted": rule.is_deleted,
    }


def _priority_key(rule: RuleModel) -> tuple[int, str, str]:
    return (_PRIORITY_ORDER.get((rule.priority or "").lower(), 99), rule.created_at.isoformat(), rule.id)


def _trigger_entity_id(event_data: dict[str, Any]) -> str | None:
    for key in _TRIGGER_ENTITY_KEYS:
        value = event_data.get(key)
        if value:
            return str(value)
    return None


def _result_status(action_results: list[ActionResult]) -> str:
    if not action_results:
        return "success"
    successes = [result.success for result in action_results]
    if all(successes):
        return "success"
    if any(successes):
        return "partial"
    return "failed"


async def _get_rule_or_404(db: AsyncSession, rule_id: str) -> RuleModel:
    result = await db.execute(select(RuleModel).where(RuleModel.id == rule_id, RuleModel.is_deleted.is_(False)))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return rule


async def _validate_chain_target(
    db: AsyncSession, chain_to_rule_id: str | None, *, self_rule_id: str | None = None
) -> None:
    if chain_to_rule_id is None:
        return
    if self_rule_id is not None and chain_to_rule_id == self_rule_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rule cannot chain to itself")
    target = await db.get(RuleModel, chain_to_rule_id)
    if target is None or target.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="chain_to_rule_id does not reference an active rule"
        )


def _apply_rule_filters(
    stmt,
    *,
    type_filter: str | None = None,
    priority: str | None = None,
    status_filter: str | None = None,
):
    stmt = stmt.where(RuleModel.is_deleted.is_(False))
    if type_filter:
        stmt = stmt.where(RuleModel.type == type_filter.strip().lower())
    if priority:
        stmt = stmt.where(RuleModel.priority == priority.strip().lower())
    if status_filter:
        normalized = status_filter.strip().lower()
        if normalized in {"active", "enabled", "true"}:
            stmt = stmt.where(RuleModel.active.is_(True))
        elif normalized in {"inactive", "disabled", "false"}:
            stmt = stmt.where(RuleModel.active.is_(False))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid rule status filter")
    return stmt


async def list_rules(
    db: AsyncSession,
    *,
    type_filter: str | None = None,
    priority: str | None = None,
    status_filter: str | None = None,
    sort: str = "created_at",
    order: str = "desc",
    page: int = 1,
    size: int = 20,
) -> PaginatedRules:
    page = max(page, 1)
    size = min(max(size, 1), 100)

    count_stmt = _apply_rule_filters(
        select(func.count(RuleModel.id)),
        type_filter=type_filter,
        priority=priority,
        status_filter=status_filter,
    )
    total = int((await db.execute(count_stmt)).scalar_one() or 0)

    column = _SORT_COLUMNS.get((sort or "created_at").strip(), RuleModel.created_at)
    sort_expr = column.asc() if (order or "desc").lower() == "asc" else column.desc()
    stmt = _apply_rule_filters(
        select(RuleModel),
        type_filter=type_filter,
        priority=priority,
        status_filter=status_filter,
    )
    stmt = stmt.order_by(sort_expr, RuleModel.id.asc()).offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    return PaginatedRules(
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
        items=[RuleSchema.model_validate(rule) for rule in result.scalars().all()],
    )


async def get_rule(db: AsyncSession, rule_id: str) -> RuleSchema:
    return RuleSchema.model_validate(await _get_rule_or_404(db, rule_id))


async def create_rule(db: AsyncSession, body: RuleCreateSchema, *, current_user: UserSchema) -> RuleSchema:
    await _validate_chain_target(db, str(body.chain_to_rule_id) if body.chain_to_rule_id else None)
    data = body.model_dump(mode="json")
    rule = RuleModel(
        name=data["name"].strip(),
        description=data.get("description"),
        type=data["type"].strip().lower(),
        priority=data["priority"].strip().lower(),
        active=bool(data.get("active", True)),
        conditions=data["conditions"],
        time_constraints=data.get("time_constraints"),
        scope=data.get("scope"),
        actions=data["actions"],
        chain_to_rule_id=data.get("chain_to_rule_id"),
        created_by=str(current_user.id),
        is_deleted=False,
    )
    db.add(rule)
    await db.flush()
    await audit_service.log(
        db,
        event_type="rule.created",
        action="create",
        resource_type="rule",
        resource_id=rule.id,
        summary=f"Created rule '{rule.name}'",
        after_state=_rule_state(rule),
        **_audit_user(current_user),
    )
    return RuleSchema.model_validate(rule)


async def update_rule(
    db: AsyncSession,
    rule_id: str,
    body: RuleUpdateSchema,
    *,
    current_user: UserSchema,
) -> RuleSchema:
    rule = await _get_rule_or_404(db, rule_id)
    data = body.model_dump(mode="json", exclude_unset=True)
    await _validate_chain_target(db, data.get("chain_to_rule_id"), self_rule_id=rule.id)
    if not data:
        return RuleSchema.model_validate(rule)

    before = _rule_state(rule)
    for field, value in data.items():
        if field in {"conditions", "actions", "time_constraints", "scope"}:
            setattr(rule, field, _dump(value))
        elif field == "chain_to_rule_id":
            rule.chain_to_rule_id = value
        elif field in {"name", "priority"} and isinstance(value, str):
            setattr(rule, field, value.strip().lower() if field == "priority" else value.strip())
        else:
            setattr(rule, field, value)
    await db.flush()
    await audit_service.log(
        db,
        event_type="rule.updated",
        action="update",
        resource_type="rule",
        resource_id=rule.id,
        summary=f"Updated rule '{rule.name}'",
        before_state=before,
        after_state=_rule_state(rule),
        **_audit_user(current_user),
    )
    return RuleSchema.model_validate(rule)


async def delete_rule(db: AsyncSession, rule_id: str, *, current_user: UserSchema) -> dict[str, Any]:
    rule = await _get_rule_or_404(db, rule_id)
    result = await db.execute(
        select(RuleModel.id, RuleModel.name).where(
            RuleModel.chain_to_rule_id == rule.id,
            RuleModel.is_deleted.is_(False),
            RuleModel.active.is_(True),
        )
    )
    dependents = [{"id": row.id, "name": row.name} for row in result.all()]
    before = _rule_state(rule)
    rule.active = False
    rule.is_deleted = True
    await db.flush()
    await audit_service.log(
        db,
        event_type="rule.deleted",
        action="delete",
        resource_type="rule",
        resource_id=rule.id,
        summary=f"Deleted rule '{rule.name}'",
        before_state=before,
        after_state=_rule_state(rule),
        metadata={"dependent_rules": dependents},
        **_audit_user(current_user),
    )
    message = "Rule deleted"
    if dependents:
        message = "Rule deleted; dependent active chains should be reviewed"
    return {"message": message, "dependent_rules": dependents}


async def toggle_rule(db: AsyncSession, rule_id: str, *, active: bool, current_user: UserSchema) -> dict[str, str]:
    rule = await _get_rule_or_404(db, rule_id)
    before = _rule_state(rule)
    rule.active = active
    await db.flush()
    await audit_service.log(
        db,
        event_type="rule.toggled",
        action="toggle",
        resource_type="rule",
        resource_id=rule.id,
        summary=f"{'Enabled' if active else 'Disabled'} rule '{rule.name}'",
        before_state=before,
        after_state=_rule_state(rule),
        **_audit_user(current_user),
    )
    return {"message": "Rule enabled" if active else "Rule disabled"}


async def duplicate_rule(db: AsyncSession, rule_id: str, *, current_user: UserSchema) -> RuleSchema:
    source = await _get_rule_or_404(db, rule_id)
    duplicate = RuleModel(
        name=f"Copy of {source.name}",
        description=source.description,
        type=source.type,
        priority=source.priority,
        active=False,
        conditions=_dump(source.conditions),
        time_constraints=_dump(source.time_constraints),
        scope=_dump(source.scope),
        actions=_dump(source.actions),
        chain_to_rule_id=source.chain_to_rule_id,
        created_by=str(current_user.id),
        is_deleted=False,
    )
    db.add(duplicate)
    await db.flush()
    await audit_service.log(
        db,
        event_type="rule.duplicated",
        action="duplicate",
        resource_type="rule",
        resource_id=duplicate.id,
        summary=f"Duplicated rule '{source.name}'",
        after_state=_rule_state(duplicate),
        metadata={"source_rule_id": source.id},
        **_audit_user(current_user),
    )
    return RuleSchema.model_validate(duplicate)


async def test_rule(db: AsyncSession, rule_id: str, body: TestPayloadSchema) -> TestResultSchema:
    rule = await _get_rule_or_404(db, rule_id)
    context = {
        **body.model_dump(mode="json", exclude_none=True),
        "event_type": "manual_test",
        "rule_id": rule.id,
        "rule_name": rule.name,
        "time_constraints": rule.time_constraints or {},
    }
    matched = await ConditionMatcher(db).match(rule.conditions, context)
    return TestResultSchema(
        rule_id=rule.id,
        matched=matched,
        matched_conditions=rule.conditions if matched else [],
        would_execute_actions=rule.actions if matched else [],
        reason="Conditions matched" if matched else "Conditions did not match",
    )


async def simulate_rule(
    db: AsyncSession,
    rule_id: str,
    *,
    date_from: date,
    date_to: date,
) -> SimulationResultSchema:
    if date_from > date_to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date_from must be before date_to")
    rule = await _get_rule_or_404(db, rule_id)
    result = await db.execute(
        select(WasteEntryModel)
        .where(WasteEntryModel.session_date >= date_from, WasteEntryModel.session_date <= date_to)
        .order_by(WasteEntryModel.timestamp.asc())
    )
    entries = result.scalars().all()
    matcher = ConditionMatcher(db)
    matched_count = 0
    projected_warnings = 0
    projected_penalties = 0
    projected_emails = 0
    sample_matches: list[dict[str, Any]] = []

    for entry in entries:
        context = await _build_context(db, "waste_entry_created", _event_data_from_entry(entry), rule)
        if not _scope_matches(rule.scope, context):
            continue
        if await matcher.match(rule.conditions, context):
            matched_count += 1
            action_types = [str(action.get("type")) for action in rule.actions or []]
            projected_warnings += action_types.count("generate_warning")
            projected_penalties += action_types.count("increase_penalty")
            projected_emails += action_types.count("send_email")
            if len(sample_matches) < 10:
                sample_matches.append(
                    {
                        "waste_entry_id": entry.id,
                        "student_id": entry.student_id,
                        "timestamp": entry.timestamp.isoformat(),
                        "weight_grams": entry.weight_grams,
                    }
                )

    return SimulationResultSchema(
        rule_id=rule.id,
        period_from=date_from,
        period_to=date_to,
        total_events_evaluated=len(entries),
        matched_count=matched_count,
        projected_warnings=projected_warnings,
        projected_penalties=projected_penalties,
        projected_emails=projected_emails,
        sample_matches=sample_matches,
    )


async def get_rule_executions(
    db: AsyncSession,
    rule_id: str,
    *,
    page: int = 1,
    size: int = 20,
) -> PaginatedExecutions:
    await _get_rule_or_404(db, rule_id)
    page = max(page, 1)
    size = min(max(size, 1), 100)
    total = int(
        (
            await db.execute(select(func.count(RuleExecutionModel.id)).where(RuleExecutionModel.rule_id == rule_id))
        ).scalar_one()
        or 0
    )
    result = await db.execute(
        select(RuleExecutionModel)
        .where(RuleExecutionModel.rule_id == rule_id)
        .order_by(RuleExecutionModel.executed_at.desc(), RuleExecutionModel.id.asc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return PaginatedExecutions(
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
        items=[RuleExecutionSchema.model_validate(row) for row in result.scalars().all()],
    )


async def get_rule_chains(db: AsyncSession) -> ChainDataSchema:
    result = await db.execute(select(RuleModel).where(RuleModel.is_deleted.is_(False)))
    rules = result.scalars().all()
    return ChainDataSchema(
        nodes=[ChainNodeSchema(id=rule.id, name=rule.name, type=rule.type) for rule in rules],
        edges=[
            ChainEdgeSchema(from_rule_id=rule.id, to_rule_id=rule.chain_to_rule_id)
            for rule in rules
            if rule.chain_to_rule_id
        ],
    )


def get_available_fields() -> list[FieldOptionSchema]:
    return [
        FieldOptionSchema(
            field="waste_grams", label="Waste grams", type="numeric", operators=["gt", "gte", "lt", "lte", "between"]
        ),
        FieldOptionSchema(
            field="meal_type",
            label="Meal type",
            type="enum",
            operators=["eq", "neq", "in", "not_in"],
            enum_values=["breakfast", "lunch", "dinner", "other"],
        ),
        FieldOptionSchema(
            field="severity",
            label="Severity",
            type="enum",
            operators=["eq", "neq", "in", "not_in"],
            enum_values=["normal", "warning", "high"],
        ),
        FieldOptionSchema(field="food_item", label="Food item", type="string", operators=["eq", "in", "contains"]),
        FieldOptionSchema(
            field="student_branch", label="Student branch", type="string", operators=["eq", "neq", "in", "not_in"]
        ),
        FieldOptionSchema(
            field="student_year", label="Student year", type="numeric", operators=["eq", "neq", "in", "between"]
        ),
        FieldOptionSchema(
            field="warning_count", label="Warning count", type="numeric", operators=["gt", "gte", "lt", "lte", "eq"]
        ),
        FieldOptionSchema(
            field="penalty_count", label="Penalty count", type="numeric", operators=["gt", "gte", "lt", "lte", "eq"]
        ),
        FieldOptionSchema(
            field="sustainability_score",
            label="Sustainability score",
            type="numeric",
            operators=["gt", "gte", "lt", "lte", "between"],
        ),
        FieldOptionSchema(
            field="frequency_count", label="Frequency count", type="numeric", operators=["gte", "gt", "eq"]
        ),
        FieldOptionSchema(
            field="avg_waste_7d", label="Average waste 7d", type="numeric", operators=["gt", "gte", "lt", "lte"]
        ),
        FieldOptionSchema(
            field="avg_waste_30d", label="Average waste 30d", type="numeric", operators=["gt", "gte", "lt", "lte"]
        ),
    ]


def get_available_operators() -> list[OperatorOptionSchema]:
    return [
        OperatorOptionSchema(operator="gt", label="Greater than", applies_to=["numeric"]),
        OperatorOptionSchema(operator="gte", label="Greater than or equal", applies_to=["numeric"]),
        OperatorOptionSchema(operator="lt", label="Less than", applies_to=["numeric"]),
        OperatorOptionSchema(operator="lte", label="Less than or equal", applies_to=["numeric"]),
        OperatorOptionSchema(operator="eq", label="Equals", applies_to=["numeric", "string", "enum"]),
        OperatorOptionSchema(operator="neq", label="Does not equal", applies_to=["numeric", "string", "enum"]),
        OperatorOptionSchema(operator="in", label="Is one of", applies_to=["string", "enum"]),
        OperatorOptionSchema(operator="not_in", label="Is not one of", applies_to=["string", "enum"]),
        OperatorOptionSchema(operator="contains", label="Contains", applies_to=["string"]),
        OperatorOptionSchema(operator="between", label="Between", applies_to=["numeric"]),
    ]


def get_available_actions() -> list[ActionOptionSchema]:
    return [
        ActionOptionSchema(
            type="generate_warning",
            label="Generate warning",
            required_params=["level", "reason"],
            optional_params=["send_email"],
        ),
        ActionOptionSchema(
            type="send_email",
            label="Send email",
            required_params=["template_id or subject+body"],
            optional_params=["recipient_override"],
        ),
        ActionOptionSchema(
            type="trigger_escalation",
            label="Trigger escalation",
            required_params=["escalated_to_role", "reason"],
            optional_params=[],
        ),
        ActionOptionSchema(
            type="increase_penalty",
            label="Increase penalty",
            required_params=["points"],
            optional_params=["reason", "send_email"],
        ),
        ActionOptionSchema(
            type="classify_student", label="Classify student", required_params=["status"], optional_params=[]
        ),
        ActionOptionSchema(
            type="create_audit_log", label="Create audit log", required_params=["summary"], optional_params=["metadata"]
        ),
    ]


async def evaluate_event(
    *,
    event_type: str,
    event_data: dict[str, Any],
    db: AsyncSession,
    arq_pool: ArqRedis | None,
) -> list[dict[str, Any]]:
    payload = dict(event_data or {})
    depth = int(payload.get("depth") or 1)
    if depth > 3:
        return []

    result = await db.execute(select(RuleModel).where(RuleModel.active.is_(True), RuleModel.is_deleted.is_(False)))
    rules = sorted(result.scalars().all(), key=_priority_key)
    evaluated_rule_ids: set[str] = set()
    outcomes: list[dict[str, Any]] = []
    for rule in rules:
        if rule.id in evaluated_rule_ids:
            continue
        outcomes.extend(
            await _evaluate_rule(
                db,
                rule,
                event_type=event_type,
                event_data=payload,
                arq_pool=arq_pool,
                depth=depth,
                evaluated_rule_ids=evaluated_rule_ids,
            )
        )

    if event_type == "waste_entry_created":
        entry_id = _trigger_entity_id(payload)
        if entry_id:
            entry = await db.get(WasteEntryModel, entry_id)
            if entry is not None:
                entry.rule_evaluated = True
    return outcomes


async def _evaluate_rule(
    db: AsyncSession,
    rule: RuleModel,
    *,
    event_type: str,
    event_data: dict[str, Any],
    arq_pool: ArqRedis | None,
    depth: int,
    evaluated_rule_ids: set[str],
) -> list[dict[str, Any]]:
    if depth > 3 or rule.id in evaluated_rule_ids:
        return []
    evaluated_rule_ids.add(rule.id)
    context = await _build_context(db, event_type, event_data, rule, depth=depth)
    matcher = ConditionMatcher(db)
    executor = ActionExecutor()
    action_results: list[ActionResult] = []
    matched = False
    error_message: str | None = None

    try:
        matched = _scope_matches(rule.scope, context) and await matcher.match(rule.conditions, context)
        if matched:
            action_results = await executor.execute(rule.actions or [], context, db, arq_pool)
            rule.execution_count += 1
            rule.last_triggered_at = _utcnow()
    except Exception as exc:  # pragma: no cover - defensive so one bad rule cannot block others
        error_message = str(exc)

    if error_message:
        result_status = "failed"
    elif not matched:
        result_status = "skipped"
    else:
        result_status = _result_status(action_results)

    execution = RuleExecutionModel(
        rule_id=rule.id,
        trigger_event_type=event_type,
        trigger_entity_id=_trigger_entity_id(event_data),
        student_id=str(context.get("student_id")) if context.get("student_id") else None,
        matched_conditions=rule.conditions if matched else [],
        executed_actions=[result.to_dict() for result in action_results],
        result_status=result_status,
        error_message=error_message,
        executed_at=_utcnow(),
    )
    db.add(execution)
    await db.flush()

    outcomes = [
        {
            "rule_id": rule.id,
            "matched": matched,
            "status": result_status,
            "execution_id": execution.id,
            "actions": [result.to_dict() for result in action_results],
            "error": error_message,
        }
    ]

    if matched and rule.chain_to_rule_id and depth < 3:
        chained = await db.get(RuleModel, rule.chain_to_rule_id)
        if chained is None or chained.is_deleted or not chained.active:
            await audit_service.log(
                db,
                event_type="rule.chain_skipped",
                action="skip",
                resource_type="rule",
                resource_id=rule.id,
                summary=f"Rule '{rule.name}' chain target is inactive or deleted",
                metadata={"chain_to_rule_id": rule.chain_to_rule_id},
            )
        else:
            outcomes.extend(
                await _evaluate_rule(
                    db,
                    chained,
                    event_type=event_type,
                    event_data={**event_data, "depth": depth + 1},
                    arq_pool=arq_pool,
                    depth=depth + 1,
                    evaluated_rule_ids=evaluated_rule_ids,
                )
            )
    return outcomes


async def _build_context(
    db: AsyncSession,
    event_type: str,
    event_data: dict[str, Any],
    rule: RuleModel,
    *,
    depth: int = 1,
) -> dict[str, Any]:
    student_id = event_data.get("student_id")
    student: StudentModel | None = None
    mapping: StudentMappingModel | None = None
    if student_id:
        result = await db.execute(
            select(StudentModel).options(selectinload(StudentModel.mapping)).where(StudentModel.id == str(student_id))
        )
        student = result.scalar_one_or_none()
        mapping = student.mapping if student else None

    return {
        "event_type": event_type,
        "depth": depth,
        "rule_id": rule.id,
        "rule_name": rule.name,
        "trigger_entity_id": _trigger_entity_id(event_data),
        "waste_grams": event_data.get("weight_grams") or event_data.get("waste_grams"),
        "weight_grams": event_data.get("weight_grams") or event_data.get("waste_grams"),
        "meal_type": event_data.get("meal_type"),
        "severity": event_data.get("severity"),
        "food_items": event_data.get("food_items") or [],
        "student_id": str(student_id) if student_id else None,
        "device_id": str(event_data.get("device_id")) if event_data.get("device_id") else None,
        "timestamp": event_data.get("timestamp"),
        "session_date": event_data.get("session_date"),
        "student_branch": mapping.branch if mapping else None,
        "student_year": mapping.year if mapping else None,
        "student_hostel": mapping.hostel if mapping else None,
        "warning_count": student.warning_count if student else event_data.get("current_warning_count"),
        "penalty_count": student.penalty_count if student else None,
        "sustainability_score": student.sustainability_score if student else None,
        "student_status": student.status if student else None,
        "time_constraints": rule.time_constraints or {},
    }


def _scope_matches(scope: dict[str, Any] | None, context: dict[str, Any]) -> bool:
    filters = (scope or {}).get("filters") or {}
    if not filters:
        return True

    key_map = {
        "branch": "student_branch",
        "year": "student_year",
        "hostel": "student_hostel",
        "status": "student_status",
        "student_id": "student_id",
        "device_id": "device_id",
        "meal_type": "meal_type",
        "severity": "severity",
    }
    for raw_key, expected in filters.items():
        context_key = key_map.get(raw_key, raw_key)
        actual = context.get(context_key)
        expected_values = expected if isinstance(expected, list | tuple | set) else [expected]
        if str(actual) not in {str(value) for value in expected_values}:
            return False
    return True


def _event_data_from_entry(entry: WasteEntryModel) -> dict[str, Any]:
    return {
        "waste_entry_id": entry.id,
        "student_id": entry.student_id,
        "device_id": entry.device_id,
        "weight_grams": entry.weight_grams,
        "meal_type": entry.meal_type,
        "food_items": entry.food_items or [],
        "severity": entry.severity,
        "session_date": entry.session_date.isoformat(),
        "timestamp": entry.timestamp.isoformat(),
    }
