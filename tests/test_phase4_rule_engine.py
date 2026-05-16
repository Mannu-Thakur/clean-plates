from __future__ import annotations

import os
from datetime import datetime

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "phase4-test-secret")

from app.models import Base
from app.models.device import DeviceModel
from app.models.rule import RuleExecutionModel
from app.models.student import StudentModel
from app.models.user import UserModel
from app.models.warning import WarningModel
from app.schemas.auth import UserSchema
from app.schemas.rules import RuleCreateSchema
from app.schemas.waste import WasteEntryCreateSchema
from app.services import rule_engine_service, waste_service


class FakeArqPool:
    def __init__(self) -> None:
        self.jobs: list[tuple] = []
        self.messages: list[tuple[str, str]] = []

    async def enqueue_job(self, *args):
        self.jobs.append(args)

    async def publish(self, channel: str, payload: str):
        self.messages.append((channel, payload))


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
        email="phase4@example.com",
        password_hash="x",
        name="Phase 4 Admin",
        role="super_admin",
        is_active=True,
    )
    device = DeviceModel(
        device_serial="pi-phase4",
        edge_node_name="Pi Phase 4",
        institution_name="CleanPlates",
        institution_code="CP",
        campus_name="Main",
        mess_name="Main Mess",
        mess_id="MESS4",
        status="online",
        is_deleted=False,
    )
    db.add_all([user, device])
    await db.flush()
    return UserSchema.model_validate(user), device


@pytest.mark.asyncio
async def test_waste_ingestion_enqueues_rule_event(db_session: AsyncSession):
    _, device = await _seed_user_and_device(db_session)
    fake_pool = FakeArqPool()

    await waste_service.create_waste_entry(
        db_session,
        WasteEntryCreateSchema(
            student_device_id="phase4-card",
            device_serial=device.device_serial,
            weight_grams=140,
            timestamp=datetime(2026, 5, 17, 13, 15),
        ),
        arq_pool=fake_pool,
    )

    assert fake_pool.jobs
    assert fake_pool.jobs[0][0] == "evaluate_event"
    assert fake_pool.jobs[0][1] == "waste_entry_created"
    assert fake_pool.jobs[0][2]["depth"] == 1
    assert fake_pool.messages[0][0] == "cleanplates:events:waste_entry_created"


@pytest.mark.asyncio
async def test_rule_engine_evaluates_event_and_executes_warning_action(db_session: AsyncSession):
    current_user, device = await _seed_user_and_device(db_session)
    rule = await rule_engine_service.create_rule(
        db_session,
        RuleCreateSchema(
            name="High lunch waste warning",
            type="threshold",
            priority="high",
            conditions=[
                {
                    "logic": "AND",
                    "conditions": [
                        {"field": "waste_grams", "operator": "gte", "value": 120},
                        {"field": "meal_type", "operator": "eq", "value": "lunch"},
                    ],
                }
            ],
            actions=[
                {
                    "type": "generate_warning",
                    "params": {"level": "level_2", "reason": "High lunch waste"},
                }
            ],
        ),
        current_user=current_user,
    )
    entry = await waste_service.create_waste_entry(
        db_session,
        WasteEntryCreateSchema(
            student_device_id="phase4-rule-card",
            device_serial=device.device_serial,
            weight_grams=150,
            timestamp=datetime(2026, 5, 17, 13, 20),
        ),
    )

    results = await rule_engine_service.evaluate_event(
        event_type="waste_entry_created",
        event_data={
            "waste_entry_id": str(entry.id),
            "student_id": str(entry.student_id),
            "device_id": str(entry.device_id),
            "weight_grams": entry.weight_grams,
            "meal_type": entry.meal_type,
            "food_items": [],
            "severity": entry.severity,
            "session_date": entry.session_date.isoformat(),
            "timestamp": entry.timestamp.isoformat(),
            "depth": 1,
        },
        db=db_session,
        arq_pool=None,
    )

    assert results[0]["matched"] is True
    warning = (await db_session.execute(select(WarningModel))).scalar_one()
    assert warning.rule_id == str(rule.id)
    assert warning.waste_entry_id == str(entry.id)
    student = await db_session.get(StudentModel, str(entry.student_id))
    await db_session.refresh(student)
    assert student.warning_count == 1
    execution = (await db_session.execute(select(RuleExecutionModel))).scalar_one()
    assert execution.result_status == "success"


def test_phase4_rule_routes_are_registered():
    from app.main import app

    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/api/v1/rules/" in paths
    assert "/api/v1/rules/{rule_id}/test" in paths
    assert "/api/v1/rules/{rule_id}/executions" in paths
