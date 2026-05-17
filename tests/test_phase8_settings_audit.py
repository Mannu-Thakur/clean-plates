from __future__ import annotations

import io
import os
import zipfile
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "phase8-test-secret")

from app.core.config import settings
from app.models import Base
from app.models.audit import AuditEventModel
from app.models.role import RoleModel
from app.models.user import UserModel
from app.schemas.auth import UserSchema
from app.schemas.config import SecurityConfigSchema
from app.schemas.roles import RoleUpdateSchema
from app.schemas.settings import UserCreateSchema, UserUpdateSchema
from app.services import audit_service, roles_service, settings_service


class FakeArqPool:
    def __init__(self) -> None:
        self.jobs: list[tuple] = []

    async def enqueue_job(self, *args):
        self.jobs.append(args)


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


async def _seed_super_admin(db: AsyncSession) -> tuple[UserSchema, UserModel]:
    user = UserModel(
        email="phase8-admin@example.com",
        password_hash="x",
        name="Phase 8 Admin",
        role="super_admin",
        is_active=True,
    )
    role = RoleModel(
        name="mess_admin",
        description="Mess administrator",
        permissions={"students": ["read"]},
        is_system=True,
    )
    db.add_all([user, role])
    await db.flush()
    return UserSchema.model_validate(user), user


@pytest.mark.asyncio
async def test_phase8_settings_user_security_logo_restore_and_roles(db_session: AsyncSession, tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "BACKUPS_DIR", str(tmp_path / "backups"))
    current_user, admin_model = await _seed_super_admin(db_session)

    created = await settings_service.create_user(
        db_session,
        UserCreateSchema(
            email="mess@example.com",
            name="Mess Admin",
            role="mess_admin",
            password="TempPass123",
        ),
        current_user=current_user,
    )
    assert created.email == "mess@example.com"

    with pytest.raises(HTTPException) as duplicate:
        await settings_service.create_user(
            db_session,
            UserCreateSchema(email="mess@example.com", name="Duplicate", role="mess_admin", password="TempPass123"),
            current_user=current_user,
        )
    assert duplicate.value.status_code == status.HTTP_409_CONFLICT

    updated = await settings_service.update_user(
        db_session,
        created.id,
        UserUpdateSchema(name="Mess Lead"),
        current_user=current_user,
    )
    assert updated.name == "Mess Lead"

    temp_password = await settings_service.reset_user_password(db_session, created.id, current_user=current_user)
    assert len(temp_password.temp_password) >= 8

    await settings_service.deactivate_user(db_session, created.id, current_user=current_user)
    deactivated = await db_session.get(UserModel, created.id)
    assert deactivated is not None and deactivated.is_active is False

    with pytest.raises(HTTPException) as self_deactivate:
        await settings_service.deactivate_user(db_session, admin_model.id, current_user=current_user)
    assert self_deactivate.value.status_code == status.HTTP_409_CONFLICT

    security = await settings_service.update_security_config(
        db_session,
        SecurityConfigSchema(access_token_expiry_minutes=45),
        current_user=current_user,
    )
    assert security.access_token_expiry_minutes == 45

    upload = UploadFile(file=io.BytesIO(b"\x89PNG\r\nphase8"), filename="logo.png")
    logo = await settings_service.upload_logo(db_session, upload, current_user=current_user)
    assert logo.logo_url.startswith("/static/uploads/logos/")
    assert (tmp_path / "uploads" / "logos").exists()

    backup_zip = tmp_path / "restore.zip"
    with zipfile.ZipFile(backup_zip, "w") as archive:
        archive.writestr("cleanplates.db", b"sqlite bytes")
    fake_pool = FakeArqPool()
    restore_upload = UploadFile(file=io.BytesIO(backup_zip.read_bytes()), filename="restore.zip")
    result = await settings_service.restore_backup(
        db_session,
        restore_upload,
        current_user=current_user,
        arq_pool=fake_pool,
    )
    assert result.success is True
    assert fake_pool.jobs[0][0] == "restore_backup_task"

    role = (await db_session.execute(select(RoleModel).where(RoleModel.name == "mess_admin"))).scalar_one()
    updated_role = await roles_service.update_role(
        db_session,
        role.id,
        RoleUpdateSchema(permissions={"students": ["read", "write"], "reports": ["export"]}),
        current_user=current_user,
    )
    assert updated_role.permissions["students"] == ["read", "write"]


@pytest.mark.asyncio
async def test_phase8_audit_filters_timeline_stats_and_export(db_session: AsyncSession, tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "BACKUPS_DIR", str(tmp_path / "backups"))
    current_user, _ = await _seed_super_admin(db_session)
    await audit_service.log(
        db_session,
        event_type="config.updated",
        action="update",
        resource_type="config",
        resource_id="security",
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role,
        summary="Updated security configuration",
        after_state={"access_token_expiry_minutes": 45},
    )
    await audit_service.log(
        db_session,
        event_type="rule.created",
        action="create",
        resource_type="rule",
        resource_id="rule-1",
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role,
        summary="Created lunch waste rule",
    )
    await audit_service.log(
        db_session,
        event_type="warning.issued",
        action="create",
        resource_type="warning",
        summary="System issued warning",
    )
    await db_session.flush()

    config_events = await audit_service.list_events(db_session, event_type="config.updated")
    assert config_events.total == 1
    assert config_events.items[0].resource_id == "security"

    search_events = await audit_service.list_events(db_session, q="lunch")
    assert search_events.total == 1
    assert search_events.items[0].event_type == "rule.created"

    stats = await audit_service.get_stats(db_session)
    assert stats.total_today == 3
    assert stats.config_changes == 1
    assert stats.rule_changes == 1
    assert stats.warning_events == 1

    timeline = await audit_service.get_timeline(db_session)
    assert any(group.user_name == "System" for group in timeline.groups)
    assert any(group.user_name == current_user.name for group in timeline.groups)

    event = (await db_session.execute(select(AuditEventModel).where(AuditEventModel.event_type == "config.updated"))).scalar_one()
    detail = await audit_service.get_event(db_session, event.id)
    assert detail.metadata is None
    assert detail.after_state == {"access_token_expiry_minutes": 45}

    file_path, filename = await audit_service.export_log(db_session, current_user=current_user)
    assert filename.endswith(".csv")
    assert Path(file_path).exists()


def test_phase8_routes_and_workers_are_registered():
    from app.main import app
    from app.workers.arq_settings import WorkerSettings

    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/api/v1/settings/users" in paths
    assert "/api/v1/settings/backups/restore" in paths
    assert "/api/v1/settings/maintenance/export-all" in paths
    assert "/api/v1/audit/" in paths
    assert "/api/v1/audit/{event_id}" in paths
    assert "/api/v1/roles/" in paths

    function_names = {function.__name__ for function in WorkerSettings.functions}
    assert {"create_backup_task", "auto_backup", "purge_old_audit_events", "restore_backup_task"} <= function_names
    assert len(WorkerSettings.cron_jobs) >= 8
