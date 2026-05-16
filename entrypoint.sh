#!/bin/bash
set -e

# ── H2-audit-fix: Staged DB restore ─────────────────────────────────────────
# If a staged restore exists (from backup restore task), replace the main DB
# before the app boots.
if [ -f "./data/staging_restore.db" ]; then
    echo "[entrypoint] Detected staging_restore.db — performing restore..."

    # Remove old WAL/SHM files to prevent corruption
    rm -f ./data/cleanplates.db-wal ./data/cleanplates.db-shm

    # Replace main DB with restored copy
    mv ./data/staging_restore.db ./data/cleanplates.db

    # Remove lock file
    rm -f ./data/restart.lock

    echo "[entrypoint] Database restore complete."
fi

# ── Ensure required directories exist ────────────────────────────────────────
mkdir -p data uploads reports backups logs

# ── Run Alembic migrations ───────────────────────────────────────────────────
echo "[entrypoint] Running database migrations..."
alembic upgrade head

# ── Start the application ───────────────────────────────────────────────────
echo "[entrypoint] Starting application..."
exec "$@"
