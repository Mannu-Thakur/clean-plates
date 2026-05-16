"""Action dispatch for matched rule definitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from arq.connections import ArqRedis
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import StudentModel
from app.models.warning import WarningModel
from app.schemas.warnings import EscalateWarningSchema, PenaltyCreateSchema, WarningCreateSchema
from app.services import audit_service, warning_service


_ACTION_PRIORITY = {
    "generate_warning": 1,
    "send_email": 2,
    "trigger_escalation": 3,
    "increase_penalty": 4,
    "classify_student": 5,
    "create_audit_log": 6,
}
_VALID_STUDENT_STATUSES = {"green", "yellow", "orange", "red"}


@dataclass(slots=True)
class ActionResult:
    action_type: str
    success: bool
    entity_id: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _action_dict(action: Any) -> dict[str, Any]:
    if isinstance(action, BaseModel):
        return action.model_dump(mode="json")
    return dict(action or {})


class ActionExecutor:
    """Execute rule actions with per-action failure isolation."""

    async def execute(
        self,
        actions: list[Any],
        context: dict[str, Any],
        db: AsyncSession,
        arq_pool: ArqRedis | None,
    ) -> list[ActionResult]:
        action_data = [_action_dict(action) for action in actions]
        action_data.sort(key=lambda action: _ACTION_PRIORITY.get(str(action.get("type")), 100))

        results: list[ActionResult] = []
        for action in action_data:
            action_type = str(action.get("type") or "").strip()
            params = dict(action.get("params") or {})
            try:
                handler = getattr(self, action_type, None)
                if handler is None:
                    raise ValueError(f"Unknown action type '{action_type}'")
                result = await handler(params, context, db, arq_pool)
            except Exception as exc:  # pragma: no cover - intentionally defensive
                result = ActionResult(action_type=action_type, success=False, error=str(exc))
            results.append(result)
        return results

    async def generate_warning(
        self,
        params: dict[str, Any],
        context: dict[str, Any],
        db: AsyncSession,
        arq_pool: ArqRedis | None,
    ) -> ActionResult:
        student_id = context.get("student_id")
        if not student_id:
            raise ValueError("generate_warning requires student_id in context")

        body = WarningCreateSchema(
            level=params.get("level") or "level_1",
            reason=params.get("reason") or f"Rule '{context.get('rule_name', 'Unnamed rule')}' triggered",
            send_email=bool(params.get("send_email", False)),
            rule_id=context.get("rule_id"),
            waste_entry_id=context.get("trigger_entity_id")
            if context.get("event_type") == "waste_entry_created"
            else None,
        )
        warning = await warning_service.create_warning(
            db,
            str(student_id),
            body,
            current_user=None,
            arq_pool=arq_pool,
            event_depth=int(context.get("depth") or 1) + 1,
        )
        return ActionResult(action_type="generate_warning", success=True, entity_id=str(warning.id))

    async def send_email(
        self,
        params: dict[str, Any],
        context: dict[str, Any],
        db: AsyncSession,
        arq_pool: ArqRedis | None,  # noqa: ARG002
    ) -> ActionResult:
        await audit_service.log(
            db,
            event_type="rule.email_stubbed",
            action="send_email",
            resource_type="rule",
            resource_id=str(context.get("rule_id")) if context.get("rule_id") else None,
            summary="Rule email action deferred until Phase 6",
            metadata={
                "student_id": context.get("student_id"),
                "template_id": params.get("template_id"),
                "subject": params.get("subject"),
                "recipient_override": params.get("recipient_override"),
            },
        )
        return ActionResult(action_type="send_email", success=True)

    async def increase_penalty(
        self,
        params: dict[str, Any],
        context: dict[str, Any],
        db: AsyncSession,
        arq_pool: ArqRedis | None,
    ) -> ActionResult:
        student_id = context.get("student_id")
        if not student_id:
            raise ValueError("increase_penalty requires student_id in context")

        body = PenaltyCreateSchema(
            points=int(params.get("points") or 1),
            reason=params.get("reason") or f"Penalty from rule '{context.get('rule_name', 'Unnamed rule')}'",
            send_email=bool(params.get("send_email", False)),
            rule_id=context.get("rule_id"),
        )
        penalty = await warning_service.create_penalty_direct(
            db,
            str(student_id),
            body,
            current_user=None,
            arq_pool=arq_pool,
            event_depth=int(context.get("depth") or 1) + 1,
        )
        return ActionResult(action_type="increase_penalty", success=True, entity_id=str(penalty.id))

    async def trigger_escalation(
        self,
        params: dict[str, Any],
        context: dict[str, Any],
        db: AsyncSession,
        arq_pool: ArqRedis | None,  # noqa: ARG002
    ) -> ActionResult:
        student_id = context.get("student_id")
        if not student_id:
            raise ValueError("trigger_escalation requires student_id in context")

        result = await db.execute(
            select(WarningModel)
            .where(WarningModel.student_id == str(student_id), WarningModel.status == "active")
            .order_by(WarningModel.created_at.desc())
            .limit(1)
        )
        warning = result.scalar_one_or_none()
        if warning is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No active warning to escalate")

        escalation = await warning_service.escalate_warning(
            db,
            warning.id,
            EscalateWarningSchema(
                escalated_to_role=params.get("escalated_to_role") or "institution_admin",
                reason=params.get("reason") or f"Escalated by rule '{context.get('rule_name', 'Unnamed rule')}'",
            ),
            current_user=None,
        )
        return ActionResult(action_type="trigger_escalation", success=True, entity_id=str(escalation.id))

    async def classify_student(
        self,
        params: dict[str, Any],
        context: dict[str, Any],
        db: AsyncSession,
        arq_pool: ArqRedis | None,  # noqa: ARG002
    ) -> ActionResult:
        student_id = context.get("student_id")
        new_status = str(params.get("status") or "").strip().lower()
        if not student_id:
            raise ValueError("classify_student requires student_id in context")
        if new_status not in _VALID_STUDENT_STATUSES:
            raise ValueError("status must be one of green, yellow, orange, red")

        student = await db.get(StudentModel, str(student_id))
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

        before = {"status": student.status, "is_status_manual": student.is_status_manual}
        student.status = new_status
        student.is_status_manual = True
        await db.flush()
        await audit_service.log(
            db,
            event_type="student.classified_by_rule",
            action="classify",
            resource_type="student",
            resource_id=student.id,
            summary=f"Classified student as {new_status}",
            before_state=before,
            after_state={"status": student.status, "is_status_manual": student.is_status_manual},
            metadata={"rule_id": context.get("rule_id")},
        )
        return ActionResult(action_type="classify_student", success=True, entity_id=student.id)

    async def create_audit_log(
        self,
        params: dict[str, Any],
        context: dict[str, Any],
        db: AsyncSession,
        arq_pool: ArqRedis | None,  # noqa: ARG002
    ) -> ActionResult:
        await audit_service.log(
            db,
            event_type="rule.action",
            action="create_audit_log",
            resource_type="student" if context.get("student_id") else "rule",
            resource_id=str(context.get("student_id") or context.get("rule_id") or ""),
            summary=params.get("summary") or f"Rule '{context.get('rule_name', 'Unnamed rule')}' action logged",
            metadata={**dict(params.get("metadata") or {}), "rule_id": context.get("rule_id")},
        )
        return ActionResult(action_type="create_audit_log", success=True)
