"""Verify that plan-required indexes exist in Alembic migrations and, optionally, SQLite.

Usage:
    python scripts/verify_indexes.py
    python scripts/verify_indexes.py --database data/cleanplates.db
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path


EXPECTED_INDEXES = {
    "ix_users_email",
    "ix_refresh_tokens_token_hash",
    "ix_refresh_tokens_user_id",
    "ix_devices_device_serial",
    "ix_devices_status",
    "ix_device_health_device_id",
    "ix_device_health_recorded_at",
    "ix_students_device_id",
    "ix_students_status",
    "ix_student_mappings_student_id",
    "ix_student_mappings_roll_number",
    "ix_student_mappings_branch",
    "ix_student_mappings_year",
    "ix_food_items_name",
    "ix_food_items_category",
    "ix_waste_entries_student_id",
    "ix_waste_entries_device_id",
    "ix_waste_entries_timestamp",
    "ix_waste_entries_session_date",
    "ix_waste_entries_meal_type",
    "ix_waste_entries_severity",
    "ix_warnings_student_id",
    "ix_warnings_status",
    "ix_warnings_created_at",
    "ix_escalations_warning_id",
    "ix_escalations_status",
    "ix_penalties_student_id",
    "ix_penalties_status",
    "ix_rules_active",
    "ix_rules_type",
    "ix_rules_priority",
    "ix_rule_executions_rule_id",
    "ix_rule_executions_student_id",
    "ix_rule_executions_executed_at",
    "ix_notifications_type",
    "ix_notifications_status",
    "ix_notifications_recipient_type",
    "ix_notifications_created_at",
    "ix_notifications_status_scheduled_at",
    "ix_email_templates_type",
    "ix_email_templates_is_default",
    "ix_reports_type",
    "ix_reports_status",
    "ix_reports_created_at",
    "ix_system_config_section",
    "ix_audit_events_event_type",
    "ix_audit_events_resource_type",
    "ix_audit_events_user_id",
    "ix_audit_events_created_at",
    "ix_aggregated_waste_period_type",
    "ix_aggregated_waste_period_start",
    "ix_aggregated_waste_scope_type",
    "ix_aggregated_waste_scope_id",
    "ix_filter_presets_user_id",
    "ix_backups_status",
    "ix_report_schedules_next_run",
    "ix_report_schedules_active_next_run",
    # email_templates — is_deleted (migration 005)
    "ix_email_templates_is_deleted",
    # notifications — is_deleted (migration 005)
    "ix_notifications_is_deleted",
    # notification_deliveries (migration 005)
    "ix_notification_deliveries_notification_id",
    "ix_notification_deliveries_recipient_id",
    "ix_notification_deliveries_status",
}


CREATE_INDEX_RE = re.compile(r"create_index\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
SQL_INDEX_RE = re.compile(r"CREATE\s+INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)", re.IGNORECASE)


def indexes_declared_in_migrations(migrations_dir: Path) -> set[str]:
    found: set[str] = set()
    for path in sorted(migrations_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        found.update(CREATE_INDEX_RE.findall(text))
        found.update(SQL_INDEX_RE.findall(text))
    return found


def indexes_in_sqlite(db_path: Path) -> set[str]:
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {db_path}")
    with sqlite3.connect(db_path) as conn:
        tables = [
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        ]
        indexes: set[str] = set()
        for table in tables:
            safe_table = table.replace("'", "''")
            indexes.update(row[1] for row in conn.execute(f"PRAGMA index_list('{safe_table}')"))
    return indexes


def report(label: str, expected: set[str], found: set[str]) -> bool:
    missing = sorted(expected - found)
    if missing:
        print(f"[FAIL] {label}: missing {len(missing)} indexes")
        for name in missing:
            print(f"  - {name}")
        return False
    print(f"[PASS] {label}: all {len(expected)} required indexes found")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, help="Optional SQLite database to inspect after migrations")
    parser.add_argument("--migrations-dir", type=Path, default=Path("alembic/versions"))
    args = parser.parse_args()

    ok = report("Alembic migrations", EXPECTED_INDEXES, indexes_declared_in_migrations(args.migrations_dir))
    if args.database:
        ok = report("SQLite database", EXPECTED_INDEXES, indexes_in_sqlite(args.database)) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
