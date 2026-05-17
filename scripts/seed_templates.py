"""Seed six default Phase 6 email templates.

Run after: alembic upgrade head, seed_roles.py, seed_admin.py
Usage: python scripts/seed_templates.py
"""

from __future__ import annotations

import asyncio

from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models.notification import EmailTemplateModel
from app.models.user import UserModel
from app.services.template_service import extract_variables


DEFAULT_TEMPLATES = [
    {
        "name": "Default Warning",
        "type": "warning",
        "subject": "CleanPlates warning for {{ student_name }}",
        "body_html": "<p>Hello {{ student_name }},</p><p>{{ reason }}</p>",
    },
    {
        "name": "Default Penalty",
        "type": "penalty",
        "subject": "CleanPlates penalty update",
        "body_html": "<p>Hello {{ student_name }},</p><p>Penalty points: {{ points }}.</p><p>{{ reason }}</p>",
    },
    {
        "name": "Appreciation",
        "type": "appreciation",
        "subject": "Great improvement, {{ student_name }}",
        "body_html": "<p>Your food waste reduction improved by {{ improvement_pct }}%.</p>",
    },
    {
        "name": "Awareness",
        "type": "awareness",
        "subject": "CleanPlates awareness note",
        "body_html": "<p>{{ message }}</p>",
    },
    {
        "name": "Custom Announcement",
        "type": "custom",
        "subject": "{{ subject }}",
        "body_html": "<p>{{ body }}</p>",
    },
    {
        "name": "Device Offline",
        "type": "device_offline",
        "subject": "Device offline: {{ device_name }}",
        "body_html": "<p>{{ device_name }} has been offline since {{ last_heartbeat }}.</p>",
    },
]


async def _template_owner(session: AsyncSession) -> str:
    result = await session.execute(select(UserModel).where(UserModel.role == "super_admin").order_by(UserModel.created_at.asc()))
    user = result.scalar_one_or_none()
    if user is not None:
        return user.id

    result = await session.execute(select(UserModel).order_by(UserModel.created_at.asc()))
    user = result.scalar_one_or_none()
    if user is not None:
        return user.id

    service_user = UserModel(
        email="template-seed@cleanplates.local",
        password_hash=await hash_password("unused-template-seed-password"),
        name="Template Seed User",
        role="super_admin",
        is_active=False,
    )
    session.add(service_user)
    await session.flush()
    return service_user.id


async def seed_templates() -> None:
    engine = create_async_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 15})

    @event.listens_for(engine.sync_engine, "connect")
    def _set_pragmas(dbapi_conn, rec):  # noqa: ARG001
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        owner_id = await _template_owner(session)
        for template_data in DEFAULT_TEMPLATES:
            result = await session.execute(
                select(EmailTemplateModel).where(
                    EmailTemplateModel.type == template_data["type"],
                    EmailTemplateModel.name == template_data["name"],
                )
            )
            template = result.scalar_one_or_none()
            variables = extract_variables(template_data["subject"], template_data["body_html"])
            if template is None:
                session.add(
                    EmailTemplateModel(
                        name=template_data["name"],
                        type=template_data["type"],
                        subject=template_data["subject"],
                        body_html=template_data["body_html"],
                        variables=variables,
                        is_default=True,
                        created_by=owner_id,
                    )
                )
                print(f"  [OK] Created {template_data['type']} template")
            else:
                template.subject = template_data["subject"]
                template.body_html = template_data["body_html"]
                template.variables = variables
                template.is_default = True
                template.is_deleted = False
                print(f"  [OK] Updated {template_data['type']} template")
        await session.commit()
    await engine.dispose()
    print("\n[DONE] Template seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed_templates())
