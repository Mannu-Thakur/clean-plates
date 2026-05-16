"""003 - Waste entries, warnings, escalations, penalties, and rules

Creates: rules, rule_executions, waste_entries, warnings, escalations, penalties.

Revision ID: 003
Revises: 002
Create Date: 2026-05-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("time_constraints", sa.JSON(), nullable=True),
        sa.Column("scope", sa.JSON(), nullable=True),
        sa.Column("actions", sa.JSON(), nullable=False),
        sa.Column("chain_to_rule_id", sa.String(36), sa.ForeignKey("rules.id"), nullable=True),
        sa.Column("execution_count", sa.Integer(), nullable=False),
        sa.Column("last_triggered_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_rules_active", "rules", ["active"])
    op.create_index("ix_rules_type", "rules", ["type"])
    op.create_index("ix_rules_priority", "rules", ["priority"])

    op.create_table(
        "waste_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("student_id", sa.String(36), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("device_id", sa.String(36), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("weight_grams", sa.Float(), nullable=False),
        sa.Column("meal_type", sa.String(20), nullable=False),
        sa.Column("food_items", sa.JSON(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("plate_image_path", sa.String(500), nullable=True),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("rule_evaluated", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("device_id", "timestamp", name="uq_waste_entries_device_timestamp"),
    )
    op.create_index("ix_waste_entries_student_id", "waste_entries", ["student_id"])
    op.create_index("ix_waste_entries_device_id", "waste_entries", ["device_id"])
    op.create_index("ix_waste_entries_timestamp", "waste_entries", ["timestamp"])
    op.create_index("ix_waste_entries_session_date", "waste_entries", ["session_date"])
    op.create_index("ix_waste_entries_meal_type", "waste_entries", ["meal_type"])
    op.create_index("ix_waste_entries_severity", "waste_entries", ["severity"])

    op.create_table(
        "rule_executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rule_id", sa.String(36), sa.ForeignKey("rules.id"), nullable=False),
        sa.Column("trigger_event_type", sa.String(50), nullable=False),
        sa.Column("trigger_entity_id", sa.String(36), nullable=True),
        sa.Column("student_id", sa.String(36), sa.ForeignKey("students.id"), nullable=True),
        sa.Column("matched_conditions", sa.JSON(), nullable=False),
        sa.Column("executed_actions", sa.JSON(), nullable=False),
        sa.Column("result_status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_rule_executions_rule_id", "rule_executions", ["rule_id"])
    op.create_index("ix_rule_executions_student_id", "rule_executions", ["student_id"])
    op.create_index("ix_rule_executions_executed_at", "rule_executions", ["executed_at"])

    op.create_table(
        "warnings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("student_id", sa.String(36), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("rule_id", sa.String(36), sa.ForeignKey("rules.id"), nullable=True),
        sa.Column("waste_entry_id", sa.String(36), sa.ForeignKey("waste_entries.id"), nullable=True),
        sa.Column("issued_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("resolved_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolution_note", sa.String(500), nullable=True),
        sa.Column("email_sent", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_warnings_student_id", "warnings", ["student_id"])
    op.create_index("ix_warnings_status", "warnings", ["status"])
    op.create_index("ix_warnings_created_at", "warnings", ["created_at"])

    op.create_table(
        "escalations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("warning_id", sa.String(36), sa.ForeignKey("warnings.id"), nullable=False),
        sa.Column("student_id", sa.String(36), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("escalated_to_role", sa.String(50), nullable=False),
        sa.Column("escalated_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reviewed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("review_note", sa.String(500), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_escalations_warning_id", "escalations", ["warning_id"])
    op.create_index("ix_escalations_status", "escalations", ["status"])

    op.create_table(
        "penalties",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("student_id", sa.String(36), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column("warning_id", sa.String(36), sa.ForeignKey("warnings.id"), nullable=True),
        sa.Column("rule_id", sa.String(36), sa.ForeignKey("rules.id"), nullable=True),
        sa.Column("issued_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("revoked_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("revoke_reason", sa.String(500), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("email_sent", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_penalties_student_id", "penalties", ["student_id"])
    op.create_index("ix_penalties_status", "penalties", ["status"])


def downgrade() -> None:
    op.drop_table("penalties")
    op.drop_table("escalations")
    op.drop_table("warnings")
    op.drop_table("rule_executions")
    op.drop_table("waste_entries")
    op.drop_table("rules")
