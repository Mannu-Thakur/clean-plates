from __future__ import annotations

import os
from datetime import datetime

import pytest
from fastapi import HTTPException, status
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "phase3-test-secret")

from app.models import Base
from app.models.device import DeviceModel
from app.models.student import StudentModel
from app.models.user import UserModel
from app.models.warning import EscalationModel, WarningModel
from app.schemas.auth import UserSchema
from app.schemas.rules import RuleCreateSchema
from app.schemas.students import MappingCreateSchema, MappingImportRowSchema
from app.schemas.warnings import (
    EscalateWarningSchema,
    PenaltyCreateSchema,
    ResolveWarningSchema,
    RevokePenaltySchema,
    ReviewEscalationSchema,
    WarningCreateSchema,
)
from app.schemas.waste import BulkWasteIngestSchema, WasteEntryCreateSchema
from app.services import student_service, warning_service, waste_service


@pytest.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):  # noqa: ARG001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


async def _seed_user_and_device(db: AsyncSession) -> tuple[UserSchema, DeviceModel]:
    user = UserModel(
        email="phase3@example.com",
        password_hash="x",
        name="Phase 3 Admin",
        role="super_admin",
        is_active=True,
    )
    device = DeviceModel(
        device_serial="pi-phase3",
        edge_node_name="Pi Phase 3",
        institution_name="CleanPlates",
        institution_code="CP",
        campus_name="Main",
        mess_name="Main Mess",
        mess_id="MESS1",
        status="online",
        is_deleted=False,
    )
    db.add_all([user, device])
    await db.flush()
    return UserSchema.model_validate(user), device


@pytest.mark.asyncio
async def test_phase3_waste_ingestion_student_stats_and_warning_lifecycle(db_session: AsyncSession):
    current_user, device = await _seed_user_and_device(db_session)

    entry = await waste_service.create_waste_entry(
        db_session,
        WasteEntryCreateSchema(
            student_device_id="card-001",
            device_serial=device.device_serial,
            weight_grams=135,
            food_items=[{"name": "rice", "grams": 90}, {"name": "dal", "grams": 45}],
            confidence_score=0.91,
            timestamp=datetime(2026, 5, 17, 13, 15),
        ),
    )

    assert entry.meal_type == "lunch"
    assert entry.severity == "warning"
    assert entry.student_device_id == "card-001"

    duplicate_result = await waste_service.bulk_sync(
        db_session,
        BulkWasteIngestSchema(
            entries=[
                WasteEntryCreateSchema(
                    student_device_id="card-001",
                    device_serial=device.device_serial,
                    weight_grams=135,
                    timestamp=datetime(2026, 5, 17, 13, 15),
                )
            ]
        ),
    )
    assert duplicate_result.inserted == 0
    assert duplicate_result.skipped == 1

    stats = await student_service.get_student_stats(db_session, str(entry.student_id), "all")
    assert stats.entry_count == 1
    assert stats.total_waste_grams == 135
    assert stats.most_wasted_food == "rice"
    assert stats.peak_meal == "lunch"

    warning = await warning_service.create_warning(
        db_session,
        str(entry.student_id),
        WarningCreateSchema(level="level_2", reason="Repeated lunch waste"),
        current_user=current_user,
    )

    student = await db_session.get(StudentModel, str(entry.student_id))
    assert student is not None
    await db_session.refresh(student)
    assert student.warning_count == 1
    assert student.status == "yellow"

    penalty = await warning_service.apply_penalty(db_session, str(warning.id), current_user=current_user)
    await db_session.refresh(student)
    assert student.warning_count == 0
    assert student.penalty_count == 1
    assert student.status == "red"
    assert penalty.points == 2

    await warning_service.revoke_penalty(
        db_session,
        str(penalty.id),
        RevokePenaltySchema(reason="Manual review cleared"),
        current_user=current_user,
    )
    await db_session.refresh(student)
    assert student.penalty_count == 0
    assert student.status == "yellow"

    direct_penalty = await warning_service.create_penalty_direct(
        db_session,
        str(entry.student_id),
        PenaltyCreateSchema(points=3, reason="Direct penalty"),
        current_user=current_user,
    )
    await db_session.refresh(student)
    assert direct_penalty.points == 3
    assert student.penalty_count == 1
    assert student.status == "red"


def test_phase3_restart_route_mapping_contract_and_rule_schema_exist():
    from app.main import app
    from app.models import RuleModel, WarningModel, WasteEntryModel

    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/api/v1/devices/{device_id}/restart" in paths
    assert "device_id" not in MappingCreateSchema.model_fields
    assert "device_id" in MappingImportRowSchema.model_fields
    assert RuleCreateSchema.model_fields["actions"].is_required()
    assert RuleModel.__tablename__ == "rules"
    assert WarningModel.__tablename__ == "warnings"
    assert WasteEntryModel.__tablename__ == "waste_entries"


@pytest.mark.asyncio
async def test_phase3_high_threshold_uses_waste_threshold_key(db_session: AsyncSession):
    _, device = await _seed_user_and_device(db_session)
    entry = await waste_service.create_waste_entry(
        db_session,
        WasteEntryCreateSchema(
            student_device_id="card-high",
            device_serial=device.device_serial,
            weight_grams=151,
            timestamp=datetime(2026, 5, 17, 13, 20),
        ),
    )
    assert entry.severity == "high"


@pytest.mark.asyncio
async def test_resolve_escalated_warning_requires_escalation_review(db_session: AsyncSession):
    current_user, _ = await _seed_user_and_device(db_session)
    student = StudentModel(device_id="card-escalated")
    db_session.add(student)
    await db_session.flush()

    warning = await warning_service.create_warning(
        db_session,
        student.id,
        WarningCreateSchema(level="level_1", reason="Needs review"),
        current_user=current_user,
    )
    escalation = await warning_service.escalate_warning(
        db_session,
        str(warning.id),
        body=EscalateWarningSchema(escalated_to_role="institution_admin", reason="Review required"),
        current_user=current_user,
    )

    with pytest.raises(HTTPException) as exc_info:
        await warning_service.resolve_warning(
            db_session,
            str(warning.id),
            ResolveWarningSchema(resolution_note="Direct resolve"),
            current_user=current_user,
        )
    assert exc_info.value.status_code == status.HTTP_409_CONFLICT

    await warning_service.review_escalation(
        db_session,
        str(escalation.id),
        ReviewEscalationSchema(decision="rejected", review_note="Resolved in review"),
        current_user=current_user,
    )
    stored_escalation = await db_session.get(EscalationModel, str(escalation.id))
    stored_warning = await db_session.get(WarningModel, str(warning.id))
    assert stored_escalation.status == "rejected"
    assert stored_warning.status == "resolved"


@pytest.mark.asyncio
async def test_bulk_sync_treats_insert_race_conflict_as_skipped(db_session: AsyncSession, monkeypatch):
    _, device = await _seed_user_and_device(db_session)

    async def _raise_conflict(*args, **kwargs):  # noqa: ARG001
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Waste entry already exists")

    monkeypatch.setattr(waste_service, "create_waste_entry", _raise_conflict)
    result = await waste_service.bulk_sync(
        db_session,
        BulkWasteIngestSchema(
            entries=[
                WasteEntryCreateSchema(
                    student_device_id="card-race",
                    device_serial=device.device_serial,
                    weight_grams=88,
                    timestamp=datetime(2026, 5, 17, 13, 30),
                )
            ]
        ),
    )

    assert result.inserted == 0
    assert result.skipped == 1
    assert result.errors == []
