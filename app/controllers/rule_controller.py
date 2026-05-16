"""Rule controller - thin dispatch layer over rule_engine_service."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserSchema
from app.schemas.rules import (
    ActionOptionSchema,
    ChainDataSchema,
    FieldOptionSchema,
    OperatorOptionSchema,
    PaginatedExecutions,
    PaginatedRules,
    RuleCreateSchema,
    RuleSchema,
    RuleUpdateSchema,
    SimulationResultSchema,
    TestPayloadSchema,
    TestResultSchema,
)
from app.services import rule_engine_service


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
    return await rule_engine_service.list_rules(
        db,
        type_filter=type_filter,
        priority=priority,
        status_filter=status_filter,
        sort=sort,
        order=order,
        page=page,
        size=size,
    )


async def get_rule(db: AsyncSession, rule_id: str) -> RuleSchema:
    return await rule_engine_service.get_rule(db, rule_id)


async def create_rule(db: AsyncSession, body: RuleCreateSchema, *, current_user: UserSchema) -> RuleSchema:
    return await rule_engine_service.create_rule(db, body, current_user=current_user)


async def update_rule(
    db: AsyncSession,
    rule_id: str,
    body: RuleUpdateSchema,
    *,
    current_user: UserSchema,
) -> RuleSchema:
    return await rule_engine_service.update_rule(db, rule_id, body, current_user=current_user)


async def delete_rule(db: AsyncSession, rule_id: str, *, current_user: UserSchema) -> dict[str, Any]:
    return await rule_engine_service.delete_rule(db, rule_id, current_user=current_user)


async def toggle_rule(db: AsyncSession, rule_id: str, *, active: bool, current_user: UserSchema) -> dict[str, str]:
    return await rule_engine_service.toggle_rule(db, rule_id, active=active, current_user=current_user)


async def duplicate_rule(db: AsyncSession, rule_id: str, *, current_user: UserSchema) -> RuleSchema:
    return await rule_engine_service.duplicate_rule(db, rule_id, current_user=current_user)


async def test_rule(db: AsyncSession, rule_id: str, body: TestPayloadSchema) -> TestResultSchema:
    return await rule_engine_service.test_rule(db, rule_id, body)


async def simulate_rule(
    db: AsyncSession,
    rule_id: str,
    *,
    date_from: date,
    date_to: date,
) -> SimulationResultSchema:
    return await rule_engine_service.simulate_rule(db, rule_id, date_from=date_from, date_to=date_to)


async def get_rule_executions(
    db: AsyncSession,
    rule_id: str,
    *,
    page: int = 1,
    size: int = 20,
) -> PaginatedExecutions:
    return await rule_engine_service.get_rule_executions(db, rule_id, page=page, size=size)


async def get_rule_chains(db: AsyncSession) -> ChainDataSchema:
    return await rule_engine_service.get_rule_chains(db)


def get_available_fields() -> list[FieldOptionSchema]:
    return rule_engine_service.get_available_fields()


def get_available_operators() -> list[OperatorOptionSchema]:
    return rule_engine_service.get_available_operators()


def get_available_actions() -> list[ActionOptionSchema]:
    return rule_engine_service.get_available_actions()
