"""006 - Phase 10 hardening indexes

Revision ID: 006
Revises: 005
Create Date: 2026-05-17
"""

from typing import Sequence, Union

from alembic import op


revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_reports_created_at ON reports (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_report_schedules_active_next_run ON report_schedules (active, next_run)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_report_schedules_active_next_run")
    op.execute("DROP INDEX IF EXISTS ix_reports_created_at")
    op.execute("DROP INDEX IF EXISTS ix_notifications_created_at")
