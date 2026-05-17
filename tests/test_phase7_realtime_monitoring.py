from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from starlette.websockets import WebSocketState

os.environ.setdefault("SECRET_KEY", "phase7-test-secret")

from app.models import Base
from app.models.device import DeviceHealthModel, DeviceModel
from app.models.notification import NotificationModel
from app.models.student import StudentMappingModel, StudentModel
from app.models.user import UserModel
from app.models.waste import WasteEntryModel
from app.schemas.auth import UserSchema
from app.services import monitoring_service, waste_service
from app.services.ws_service import ConnectionManager


class FakeArqPool:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    async def publish(self, channel: str, payload: str):
        self.messages.append((channel, payload))


class FakeWebSocket:
    def __init__(self) -> None:
        self.application_state = WebSocketState.CONNECTING
        self.sent: list[dict] = []
        self.closed: tuple[int, str | None] | None = None

    async def accept(self) -> None:
        self.application_state = WebSocketState.CONNECTED

    async def close(self, code: int = 1000, reason: str | None = None) -> None:
        self.application_state = WebSocketState.DISCONNECTED
        self.closed = (code, reason)

    async def send_json(self, payload: dict) -> None:
        self.sent.append(payload)


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


async def _seed_phase7_data(db: AsyncSession) -> tuple[UserSchema, StudentModel, DeviceModel]:
    user = UserModel(
        email="phase7@example.com",
        password_hash="x",
        name="Phase 7 Admin",
        role="super_admin",
        is_active=True,
    )
    device = DeviceModel(
        device_serial="pi-phase7",
        edge_node_name="Pi Phase 7",
        institution_name="CleanPlates",
        institution_code="CP",
        campus_name="Main",
        mess_name="Main Mess",
        mess_id="MESS7",
        status="online",
        last_heartbeat=datetime.now(UTC).replace(tzinfo=None),
        is_deleted=False,
    )
    student = StudentModel(device_id="phase7-card", status="green")
    db.add_all([user, device, student])
    await db.flush()
    db.add(
        StudentMappingModel(
            student_id=student.id,
            device_id=student.device_id,
            name="Phase Seven Student",
            roll_number="P7-001",
            branch="CSE",
            year=3,
            hostel="A",
            mapped_by=user.id,
        )
    )
    db.add(
        DeviceHealthModel(
            device_id=device.id,
            cpu_percent=42,
            ram_percent=38,
            temperature=46,
            storage_percent=52,
            connectivity=True,
            recorded_at=datetime.now(UTC).replace(tzinfo=None),
        )
    )
    await db.flush()
    return UserSchema.model_validate(user), student, device


@pytest.mark.asyncio
async def test_phase7_monitoring_reads_statuses_and_acknowledges_alerts(db_session: AsyncSession):
    current_user, student, device = await _seed_phase7_data(db_session)
    db_session.add(
        WasteEntryModel(
            student_id=student.id,
            device_id=device.id,
            weight_grams=126,
            meal_type="lunch",
            food_items=[{"name": "rice", "grams": 126}],
            session_date=datetime.now(UTC).date(),
            timestamp=datetime.now(UTC).replace(tzinfo=None),
            severity="warning",
        )
    )
    notification = NotificationModel(
        type="warning",
        channel="dashboard",
        subject="Waste alert",
        body="Please review",
        recipient_type="all",
        recipient_ids=[],
        status="sent",
        is_read=False,
    )
    db_session.add(notification)
    await db_session.flush()

    recent = await monitoring_service.get_recent_entries(db_session, limit=5)
    assert len(recent) == 1
    assert recent[0].student_name == "Phase Seven Student"

    statuses = await monitoring_service.get_device_statuses(db_session)
    assert statuses[0].status == "online"
    assert statuses[0].cpu_percent == 42

    device.last_heartbeat = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=30)
    statuses = await monitoring_service.get_device_statuses(db_session)
    assert statuses[0].status == "offline"

    await monitoring_service.acknowledge_alert(db_session, notification.id, current_user=current_user)
    await db_session.refresh(notification)
    assert notification.is_read is True


@pytest.mark.asyncio
async def test_phase7_websocket_fanout_filters_pause_and_publish_channels():
    manager = ConnectionManager("redis://unused")
    websocket = FakeWebSocket()
    current_user = UserSchema(
        id="user-1",
        email="phase7@example.com",
        name="Phase 7 Admin",
        role="super_admin",
        is_active=True,
    )

    await manager.connect(websocket, "monitoring", current_user)
    assert websocket.sent[-1]["type"] == "connected"

    await manager.handle_client_message(websocket, {"type": "filter", "meal_type": "lunch"})
    count_after_filter = len(websocket.sent)
    await manager._handle_pubsub_message(
        {
            "type": "message",
            "channel": "cleanplates:events:waste_entry_created",
            "data": json.dumps(
                {
                    "event_type": "waste_entry_created",
                    "waste_entry_id": "entry-dinner",
                    "meal_type": "dinner",
                    "weight_grams": 100,
                }
            ),
        }
    )
    assert len(websocket.sent) == count_after_filter

    await manager._handle_pubsub_message(
        {
            "type": "message",
            "channel": "cleanplates:events:waste_entry_created",
            "data": json.dumps(
                {
                    "event_type": "waste_entry_created",
                    "waste_entry_id": "entry-lunch",
                    "meal_type": "lunch",
                    "weight_grams": 125,
                }
            ),
        }
    )
    assert websocket.sent[-1]["type"] == "waste_entry"
    assert websocket.sent[-1]["waste_entry_id"] == "entry-lunch"

    await manager.handle_client_message(websocket, {"type": "pause"})
    count_after_pause = len(websocket.sent)
    await manager._handle_pubsub_message(
        {
            "type": "message",
            "channel": "cleanplates:events:waste_entry_created",
            "data": json.dumps(
                {
                    "event_type": "waste_entry_created",
                    "waste_entry_id": "entry-queued",
                    "meal_type": "lunch",
                    "weight_grams": 135,
                }
            ),
        }
    )
    assert len(websocket.sent) == count_after_pause

    await manager.handle_client_message(websocket, {"type": "resume"})
    assert websocket.sent[-2]["action"] == "resume"
    assert websocket.sent[-1]["waste_entry_id"] == "entry-queued"

    fake_redis = FakeArqPool()
    await manager.broadcast_to_room("dashboard", {"type": "kpi_update", "writes": 3}, redis=fake_redis)
    assert fake_redis.messages[0][0] == "cleanplates:ws:dashboard"
    assert json.loads(fake_redis.messages[0][1])["type"] == "kpi_update"
    await manager.disconnect(websocket)


@pytest.mark.asyncio
async def test_phase7_heartbeat_publishes_realtime_device_event(db_session: AsyncSession):
    _, _, device = await _seed_phase7_data(db_session)
    fake_pool = FakeArqPool()

    from app.schemas.waste import HeartbeatPayload

    await waste_service.ml_heartbeat(
        db_session,
        HeartbeatPayload(cpu_percent=51, ram_percent=49, temperature=45, storage_percent=60, connectivity=True),
        device=device,
        arq_pool=fake_pool,
    )

    assert fake_pool.messages[0][0] == "cleanplates:events:device_heartbeat"
    payload = json.loads(fake_pool.messages[0][1])
    assert payload["event_type"] == "device_heartbeat"
    assert payload["device_id"] == device.id
    assert payload["cpu_percent"] == 51


def test_phase7_routes_are_registered():
    from app.main import app

    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/api/v1/monitoring/current-session" in paths
    assert "/api/v1/monitoring/recent-entries" in paths
    assert "/api/v1/monitoring/device-statuses" in paths
    assert "/api/v1/monitoring/alerts/{notif_id}/acknowledge" in paths
    assert "/ws/dashboard" in paths
    assert "/ws/monitoring" in paths
