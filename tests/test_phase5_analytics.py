from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException, status
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "phase5-test-secret")

from app.models import Base
from app.models.aggregated_waste import AggregatedWasteModel
from app.models.device import DeviceModel
from app.models.student import StudentMappingModel, StudentModel
from app.models.user import UserModel
from app.models.warning import PenaltyModel, WarningModel
from app.models.waste import WasteEntryModel
from app.schemas.auth import UserSchema
from app.schemas.filter_presets import FilterPresetCreateSchema, FilterPresetUpdateSchema
from app.services import aggregation_service, analytics_service, filter_preset_service


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


async def _seed_user(db: AsyncSession, email: str = "phase5@example.com") -> UserSchema:
    user = UserModel(
        email=email,
        password_hash="x",
        name=email.split("@")[0],
        role="super_admin",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return UserSchema.model_validate(user)


async def _seed_device(db: AsyncSession, *, serial: str = "pi-phase5") -> DeviceModel:
    device = DeviceModel(
        device_serial=serial,
        edge_node_name=f"Pi {serial}",
        institution_name="CleanPlates",
        institution_code="CP",
        campus_name="Main",
        mess_name="Main Mess",
        mess_id="MESS5",
        status="online",
        is_deleted=False,
    )
    db.add(device)
    await db.flush()
    return device


async def _seed_student(
    db: AsyncSession,
    current_user: UserSchema,
    *,
    card_id: str,
    name: str,
    branch: str = "CSE",
    year: int = 2,
) -> StudentModel:
    student = StudentModel(device_id=card_id, status="green", sustainability_score=95.0)
    db.add(student)
    await db.flush()
    db.add(
        StudentMappingModel(
            student_id=student.id,
            device_id=student.device_id,
            name=name,
            roll_number=f"R-{card_id}",
            branch=branch,
            year=year,
            hostel="A",
            mapped_by=str(current_user.id),
        )
    )
    await db.flush()
    return student


@pytest.mark.asyncio
async def test_phase5_analytics_services_handle_filters_and_rankings(db_session: AsyncSession):
    current_user = await _seed_user(db_session)
    device = await _seed_device(db_session)
    student_a = await _seed_student(db_session, current_user, card_id="card-a", name="Alice", branch="CSE")
    student_b = await _seed_student(db_session, current_user, card_id="card-b", name="Bob", branch="ECE")

    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    yesterday = today - timedelta(days=1)
    db_session.add_all(
        [
            WasteEntryModel(
                student_id=student_a.id,
                device_id=device.id,
                weight_grams=120,
                meal_type="lunch",
                food_items=[{"name": "rice", "grams": 80}, {"name": "dal", "grams": 40}],
                session_date=today,
                timestamp=datetime.combine(today, datetime.min.time()).replace(hour=13),
                severity="warning",
            ),
            WasteEntryModel(
                student_id=student_a.id,
                device_id=device.id,
                weight_grams=80,
                meal_type="breakfast",
                food_items=[{"name": "rice"}],
                session_date=yesterday,
                timestamp=datetime.combine(yesterday, datetime.min.time()).replace(hour=8),
                severity="normal",
            ),
            WasteEntryModel(
                student_id=student_b.id,
                device_id=device.id,
                weight_grams=220,
                meal_type="dinner",
                food_items=[{"name": "roti"}, {"name": "sabzi"}],
                session_date=today,
                timestamp=datetime.combine(today, datetime.min.time()).replace(hour=20),
                severity="high",
            ),
        ]
    )
    await db_session.flush()

    meal_distribution = await analytics_service.get_meal_distribution(db_session, period="all")
    assert {item.meal_type: item.total_grams for item in meal_distribution.data} == {
        "dinner": 220.0,
        "lunch": 120.0,
        "breakfast": 80.0,
    }

    food_ranking = await analytics_service.get_food_waste_distribution(db_session, period="all")
    assert food_ranking.data[0].food_name == "rice"
    assert food_ranking.data[0].total_grams == 160.0

    contributors = await analytics_service.get_top_contributors(db_session, period="all", limit=2)
    assert contributors.data[0].name == "Bob"
    assert contributors.data[0].total_waste_grams == 220.0

    ece_contributors = await analytics_service.get_top_contributors(db_session, period="all", branch="ECE")
    assert len(ece_contributors.data) == 1
    assert ece_contributors.data[0].device_id == "card-b"

    card_contributors = await analytics_service.get_top_contributors(db_session, period="all", device_id="card-a")
    assert len(card_contributors.data) == 1
    assert card_contributors.data[0].device_id == "card-a"

    peaks = await analytics_service.get_peak_waste(db_session, period="all")
    assert peaks.peak_hour == 20
    assert peaks.peak_meal == "dinner"

    overview = await analytics_service.get_overview(db_session, period="all")
    assert overview.total_active_students == 2
    assert overview.total_waste_month_grams >= 420.0
    assert overview.active_devices == 1

    comparison = await analytics_service.get_trends(db_session, trend_type="monthly_comparison")
    assert comparison.current_label
    assert comparison.previous_label

    scores = await analytics_service.get_sustainability_scores(db_session)
    assert scores.excellent_count == 2
    assert scores.overall_avg == 95.0


@pytest.mark.asyncio
async def test_phase5_filter_presets_are_owner_scoped(db_session: AsyncSession):
    owner = await _seed_user(db_session, "owner@example.com")
    other = await _seed_user(db_session, "other@example.com")

    created = await filter_preset_service.save_preset(
        db_session,
        FilterPresetCreateSchema(name="Lunch CSE", filter_state={"period": "7d", "branch": "CSE"}),
        current_user=owner,
    )
    assert created.name == "Lunch CSE"
    assert (await filter_preset_service.list_presets(db_session, current_user=owner))[0].id == created.id

    updated = await filter_preset_service.update_preset(
        db_session,
        str(created.id),
        FilterPresetUpdateSchema(name="Lunch CSE Focus"),
        current_user=owner,
    )
    assert updated.name == "Lunch CSE Focus"

    with pytest.raises(HTTPException) as null_exc:
        await filter_preset_service.update_preset(
            db_session,
            str(created.id),
            FilterPresetUpdateSchema(filter_state=None),
            current_user=owner,
        )
    assert null_exc.value.status_code == status.HTTP_400_BAD_REQUEST

    with pytest.raises(HTTPException) as exc_info:
        await filter_preset_service.get_preset(db_session, str(created.id), current_user=other)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    await filter_preset_service.delete_preset(db_session, str(created.id), current_user=owner)
    assert await filter_preset_service.list_presets(db_session, current_user=owner) == []


@pytest.mark.asyncio
async def test_phase5_aggregation_reconciles_status_and_fires_offline_once(db_session: AsyncSession):
    current_user = await _seed_user(db_session)
    device = await _seed_device(db_session)
    device.last_heartbeat = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=30)
    student = await _seed_student(db_session, current_user, card_id="card-status", name="Status Student")
    student.warning_count = 42
    student.penalty_count = 42

    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    db_session.add_all(
        [
            WasteEntryModel(
                student_id=student.id,
                device_id=device.id,
                weight_grams=180,
                meal_type="lunch",
                food_items=[{"name": "rice", "grams": 180}],
                session_date=today,
                timestamp=datetime.combine(today, datetime.min.time()).replace(hour=13),
                severity="high",
            ),
            WarningModel(student_id=student.id, level="level_1", reason="Active warning", status="active"),
            PenaltyModel(student_id=student.id, points=2, reason="Active penalty", status="active"),
        ]
    )
    await db_session.flush()

    await aggregation_service.update_student_status(db_session, student.id)
    await db_session.refresh(student)
    assert student.warning_count == 1
    assert student.penalty_count == 1
    assert student.status == "red"

    warning = (await db_session.execute(select(WarningModel))).scalar_one()
    penalty = (await db_session.execute(select(PenaltyModel))).scalar_one()
    warning.status = "resolved"
    penalty.status = "revoked"
    student.status = "orange"
    student.is_status_manual = True
    await aggregation_service.update_student_status(db_session, student.id)
    await db_session.refresh(student)
    assert student.warning_count == 0
    assert student.penalty_count == 0
    assert student.status == "orange"

    fake_pool = FakeArqPool()
    transitioned = await aggregation_service.check_device_offline_status(db_session, arq_pool=fake_pool)
    assert transitioned == 1
    assert device.status == "offline"
    assert fake_pool.jobs[0][0] == "evaluate_event"
    assert fake_pool.jobs[0][1] == "device_offline"

    transitioned_again = await aggregation_service.check_device_offline_status(db_session, arq_pool=fake_pool)
    assert transitioned_again == 0
    assert len(fake_pool.jobs) == 1

    writes = await aggregation_service.run_daily_aggregation(db_session, today, force=True)
    assert writes > 0
    writes_again = await aggregation_service.run_daily_aggregation(db_session, today, force=True)
    assert writes_again == 0
    aggregate_rows = (await db_session.execute(select(AggregatedWasteModel))).scalars().all()
    assert any(row.scope_type == "global" and row.total_waste_grams == 180 for row in aggregate_rows)
    assert any(row.scope_type == "branch" and row.scope_id == "CSE" for row in aggregate_rows)


def test_phase5_routes_and_workers_are_registered():
    from app.main import app
    from app.workers.arq_settings import WorkerSettings

    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/api/v1/analytics/overview" in paths
    assert "/api/v1/analytics/trends" in paths
    assert "/api/v1/filters/presets" in paths

    function_names = {function.__name__ for function in WorkerSettings.functions}
    assert {"evaluate_event", "run_hourly_aggregation", "check_device_offline_status"} <= function_names
    assert len(WorkerSettings.cron_jobs) >= 4
