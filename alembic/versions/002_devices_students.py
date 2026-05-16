"""002 - Devices, students, mappings, and food items

Creates: devices, device_health, students, student_mappings, food_items.

Revision ID: 002
Revises: 001
Create Date: 2026-05-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("device_serial", sa.String(100), nullable=False),
        sa.Column("edge_node_name", sa.String(100), nullable=False),
        sa.Column("institution_name", sa.String(200), nullable=False),
        sa.Column("institution_code", sa.String(50), nullable=False),
        sa.Column("campus_name", sa.String(100), nullable=False),
        sa.Column("mess_name", sa.String(100), nullable=False),
        sa.Column("mess_id", sa.String(50), nullable=False),
        sa.Column("hostel_name", sa.String(100), nullable=True),
        sa.Column("hostel_block", sa.String(50), nullable=True),
        sa.Column("floor_number", sa.Integer(), nullable=True),
        sa.Column("wing_section", sa.String(50), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("meal_capacity_per_day", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("mac_address", sa.String(17), nullable=True),
        sa.Column("firmware_version", sa.String(50), nullable=True),
        sa.Column("os_version", sa.String(100), nullable=True),
        sa.Column("last_heartbeat", sa.DateTime(), nullable=True),
        sa.Column("last_sync", sa.DateTime(), nullable=True),
        sa.Column("active_since", sa.DateTime(), nullable=True),
        sa.Column("managed_by", sa.String(100), nullable=True),
        sa.Column("admin_contact", sa.String(200), nullable=True),
        sa.Column("api_key_hash", sa.String(255), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("device_serial", name="uq_devices_device_serial"),
    )
    op.create_index("ix_devices_device_serial", "devices", ["device_serial"])
    op.create_index("ix_devices_status", "devices", ["status"])
    op.create_index("ix_devices_api_key_hash", "devices", ["api_key_hash"])

    op.create_table(
        "device_health",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("device_id", sa.String(36), sa.ForeignKey("devices.id"), nullable=False),
        sa.Column("cpu_percent", sa.Float(), nullable=False),
        sa.Column("ram_percent", sa.Float(), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("storage_percent", sa.Float(), nullable=True),
        sa.Column("connectivity", sa.Boolean(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_device_health_device_id", "device_health", ["device_id"])
    op.create_index("ix_device_health_recorded_at", "device_health", ["recorded_at"])

    op.create_table(
        "students",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("device_id", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("is_status_manual", sa.Boolean(), nullable=False),
        sa.Column("sustainability_score", sa.Float(), nullable=False),
        sa.Column("warning_count", sa.Integer(), nullable=False),
        sa.Column("penalty_count", sa.Integer(), nullable=False),
        sa.Column("total_waste_grams", sa.Float(), nullable=False),
        sa.Column("avg_waste_grams", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("device_id", name="uq_students_device_id"),
    )
    op.create_index("ix_students_device_id", "students", ["device_id"])
    op.create_index("ix_students_status", "students", ["status"])

    op.create_table(
        "student_mappings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("student_id", sa.String(36), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("device_id", sa.String(100), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("roll_number", sa.String(50), nullable=False),
        sa.Column("branch", sa.String(50), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("hostel", sa.String(100), nullable=True),
        sa.Column("room_number", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("mapped_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("mapped_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("student_id", name="uq_student_mappings_student_id"),
    )
    op.create_index("ix_student_mappings_student_id", "student_mappings", ["student_id"])
    op.create_index("ix_student_mappings_device_id", "student_mappings", ["device_id"])
    op.create_index("ix_student_mappings_roll_number", "student_mappings", ["roll_number"])
    op.create_index("ix_student_mappings_branch", "student_mappings", ["branch"])
    op.create_index("ix_student_mappings_year", "student_mappings", ["year"])

    op.create_table(
        "food_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_food_items_name", "food_items", ["name"])
    op.create_index("ix_food_items_category", "food_items", ["category"])


def downgrade() -> None:
    op.drop_table("food_items")
    op.drop_table("student_mappings")
    op.drop_table("students")
    op.drop_table("device_health")
    op.drop_table("devices")
