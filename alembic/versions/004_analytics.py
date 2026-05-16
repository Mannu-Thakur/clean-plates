"""004 - Analytics aggregates and filter presets

Creates: aggregated_waste, filter_presets.

Revision ID: 004
Revises: 003
Create Date: 2026-05-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "aggregated_waste",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("period_type", sa.String(20), nullable=False),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("scope_type", sa.String(20), nullable=False),
        sa.Column("scope_id", sa.String(100), nullable=True),
        sa.Column("total_waste_grams", sa.Float(), nullable=False),
        sa.Column("avg_waste_grams", sa.Float(), nullable=False),
        sa.Column("entry_count", sa.Integer(), nullable=False),
        sa.Column("student_count", sa.Integer(), nullable=True),
        sa.Column("peak_hour", sa.Integer(), nullable=True),
        sa.Column("computed_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "period_type",
            "period_start",
            "scope_type",
            "scope_id",
            name="uq_aggregated_waste_period_scope",
        ),
    )
    op.create_index("ix_aggregated_waste_period_type", "aggregated_waste", ["period_type"])
    op.create_index("ix_aggregated_waste_period_start", "aggregated_waste", ["period_start"])
    op.create_index("ix_aggregated_waste_scope_type", "aggregated_waste", ["scope_type"])
    op.create_index("ix_aggregated_waste_scope_id", "aggregated_waste", ["scope_id"])

    op.create_table(
        "filter_presets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("filter_state", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_filter_presets_user_id", "filter_presets", ["user_id"])


def downgrade() -> None:
    op.drop_table("filter_presets")
    op.drop_table("aggregated_waste")
