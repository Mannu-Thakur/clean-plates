"""Rule engine router."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import rule_controller
from app.middleware.db import get_db_session
from app.middleware.rbac import require_roles
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


router = APIRouter(prefix="/rules", tags=["Rules"])

RULE_ADMIN_ROLES = ("super_admin", "institution_admin")


@router.get("/", response_model=PaginatedRules)
async def list_rules(
    type_filter: str | None = Query(default=None, alias="type"),
    priority: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: UserSchema = Depends(require_roles(*RULE_ADMIN_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await rule_controller.list_rules(
        db,
        type_filter=type_filter,
        priority=priority,
        status_filter=status_filter,
        sort=sort,
        order=order,
        page=page,
        size=size,
    )


@router.post("/", response_model=RuleSchema, status_code=201)
async def create_rule(
    body: RuleCreateSchema,
    current_user: UserSchema = Depends(require_roles(*RULE_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await rule_controller.create_rule(db, body, current_user=current_user)


@router.get("/metadata/fields", response_model=list[FieldOptionSchema])
async def get_available_fields(
    current_user: UserSchema = Depends(require_roles(*RULE_ADMIN_ROLES)),  # noqa: ARG001
):
    return rule_controller.get_available_fields()


@router.get("/metadata/operators", response_model=list[OperatorOptionSchema])
async def get_available_operators(
    current_user: UserSchema = Depends(require_roles(*RULE_ADMIN_ROLES)),  # noqa: ARG001
):
    return rule_controller.get_available_operators()


@router.get("/metadata/actions", response_model=list[ActionOptionSchema])
async def get_available_actions(
    current_user: UserSchema = Depends(require_roles(*RULE_ADMIN_ROLES)),  # noqa: ARG001
):
    return rule_controller.get_available_actions()


@router.get("/chains", response_model=ChainDataSchema)
async def get_rule_chains(
    current_user: UserSchema = Depends(require_roles(*RULE_ADMIN_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await rule_controller.get_rule_chains(db)


@router.get("/{rule_id}", response_model=RuleSchema)
async def get_rule(
    rule_id: UUID,
    current_user: UserSchema = Depends(require_roles(*RULE_ADMIN_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await rule_controller.get_rule(db, str(rule_id))


@router.patch("/{rule_id}", response_model=RuleSchema)
async def update_rule(
    rule_id: UUID,
    body: RuleUpdateSchema,
    current_user: UserSchema = Depends(require_roles(*RULE_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await rule_controller.update_rule(db, str(rule_id), body, current_user=current_user)


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: UUID,
    current_user: UserSchema = Depends(require_roles(*RULE_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    return await rule_controller.delete_rule(db, str(rule_id), current_user=current_user)


@router.post("/{rule_id}/toggle")
async def toggle_rule(
    rule_id: UUID,
    active: bool = Body(..., embed=True),
    current_user: UserSchema = Depends(require_roles(*RULE_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    return await rule_controller.toggle_rule(db, str(rule_id), active=active, current_user=current_user)


@router.post("/{rule_id}/duplicate", response_model=RuleSchema)
async def duplicate_rule(
    rule_id: UUID,
    current_user: UserSchema = Depends(require_roles(*RULE_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db_session),
):
    return await rule_controller.duplicate_rule(db, str(rule_id), current_user=current_user)


@router.post("/{rule_id}/test", response_model=TestResultSchema)
async def test_rule(
    rule_id: UUID,
    body: TestPayloadSchema,
    current_user: UserSchema = Depends(require_roles(*RULE_ADMIN_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await rule_controller.test_rule(db, str(rule_id), body)


@router.post("/{rule_id}/simulate", response_model=SimulationResultSchema)
async def simulate_rule(
    rule_id: UUID,
    date_from: date = Query(...),
    date_to: date = Query(...),
    current_user: UserSchema = Depends(require_roles(*RULE_ADMIN_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await rule_controller.simulate_rule(db, str(rule_id), date_from=date_from, date_to=date_to)


@router.get("/{rule_id}/executions", response_model=PaginatedExecutions)
async def get_rule_executions(
    rule_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: UserSchema = Depends(require_roles(*RULE_ADMIN_ROLES)),  # noqa: ARG001
    db: AsyncSession = Depends(get_db_session),
):
    return await rule_controller.get_rule_executions(db, str(rule_id), page=page, size=size)
