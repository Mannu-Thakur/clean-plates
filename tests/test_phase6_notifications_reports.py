from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "phase6-test-secret")

from app.models import Base
from app.models.device import DeviceModel
from app.models.student import StudentMappingModel, StudentModel
from app.models.user import UserModel
from app.models.waste import WasteEntryModel
from app.schemas.auth import UserSchema
from app.schemas.config import ThresholdSchema
from app.schemas.notifications import NotificationCreateSchema
from app.schemas.reports import ReportConfigSchema, ScheduleCreateSchema
from app.schemas.templates import SampleDataSchema, TemplateCreateSchema
from app.services import config_service, notification_service, report_service, template_service


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


async def _seed_user_student_device(db: AsyncSession) -> tuple[UserSchema, StudentModel, DeviceModel]:
    user = UserModel(
        email="phase6@example.com",
        password_hash="x",
        name="Phase 6 Admin",
        role="super_admin",
        is_active=True,
    )
    device = DeviceModel(
        device_serial="pi-phase6",
        edge_node_name="Pi Phase 6",
        institution_name="CleanPlates",
        institution_code="CP",
        campus_name="Main",
        mess_name="Main Mess",
        mess_id="MESS6",
        status="online",
        is_deleted=False,
    )
    student = StudentModel(device_id="phase6-card", status="green")
    db.add_all([user, device, student])
    await db.flush()
    db.add(
        StudentMappingModel(
            student_id=student.id,
            device_id=student.device_id,
            name="Phase Six Student",
            roll_number="P6-001",
            branch="CSE",
            year=3,
            hostel="A",
            email="student@example.com",
            mapped_by=user.id,
        )
    )
    await db.flush()
    return UserSchema.model_validate(user), student, device


@pytest.mark.asyncio
async def test_phase6_templates_config_notifications_and_reports(db_session: AsyncSession):
    current_user, student, device = await _seed_user_student_device(db_session)

    thresholds = await config_service.update_config(
        db_session,
        "thresholds",
        ThresholdSchema(waste_threshold_grams=175).model_dump(),
        current_user=current_user,
    )
    assert thresholds["waste_threshold_grams"] == 175.0

    template = await template_service.create_template(
        db_session,
        TemplateCreateSchema(
            name="Warning Custom",
            type="warning",
            subject="Warning for {{ student_name }}",
            body_html="<p>{{ student_name }} wasted {{ waste_grams }}g.</p>",
        ),
        current_user=current_user,
    )
    preview = await template_service.preview_template(
        db_session,
        str(template.id),
        SampleDataSchema(variables={"student_name": "Asha", "waste_grams": 120}),
    )
    assert "Asha wasted 120g" in preview.html

    notification = await notification_service.send_notification(
        db_session,
        NotificationCreateSchema(
            type="warning",
            channel="both",
            subject="Heads up",
            body="<p>Hello {{ student_name }}</p>",
            recipient_type="individual",
            recipient_ids=[student.id],
        ),
        current_user=current_user,
        arq_pool=None,
    )
    assert notification.status == "sent"
    delivery = await notification_service.get_delivery_status(db_session, str(notification.id))
    assert delivery.delivered == 2
    assert delivery.failed == 0

    db_session.add(
        WasteEntryModel(
            student_id=student.id,
            device_id=device.id,
            weight_grams=132,
            meal_type="lunch",
            food_items=[{"name": "rice", "grams": 132}],
            session_date=datetime.now(UTC).date(),
            timestamp=datetime.now(UTC).replace(tzinfo=None),
            severity="warning",
        )
    )
    await db_session.flush()
    report = await report_service.generate_report(
        db_session,
        ReportConfigSchema(type="daily", format="csv"),
        current_user=current_user,
        arq_pool=None,
    )
    assert report.status == "ready"
    report_path, filename = await report_service.get_report_file(db_session, str(report.id))
    assert filename.endswith(".csv")
    assert Path(report_path).exists()
    Path(report_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_phase6_schedule_next_run_uses_timezone(db_session: AsyncSession):
    current_user, _, _ = await _seed_user_student_device(db_session)
    schedule = await report_service.create_schedule(
        db_session,
        ScheduleCreateSchema(
            report_type="daily",
            format="pdf",
            frequency="daily",
            time_of_day="08:00",
            auto_email=False,
        ),
        current_user=current_user,
    )
    assert schedule.next_run is not None


def test_phase6_routes_and_workers_are_registered():
    from app.main import app
    from app.workers.arq_settings import WorkerSettings

    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/api/v1/notifications/" in paths
    assert "/api/v1/notifications/{notif_id}/delivery" in paths
    assert "/api/v1/templates/{template_id}/preview" in paths
    assert "/api/v1/config/branches" in paths
    assert "/api/v1/reports/generate" in paths
    assert "/api/v1/reports/schedules" in paths

    function_names = {function.__name__ for function in WorkerSettings.functions}
    assert {"generate_report_task", "send_notification_task", "send_email_task"} <= function_names
