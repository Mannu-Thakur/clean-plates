#!/usr/bin/env bash
set -euo pipefail

cd /app

sqlite_path_from_url() {
    local url="${DATABASE_URL:-sqlite+aiosqlite:///./data/cleanplates.db}"
    local prefix="sqlite+aiosqlite:///"

    if [[ "${url}" != "${prefix}"* ]]; then
        echo ""
        return 0
    fi

    local path="${url#${prefix}}"
    if [[ "${path}" == ":memory:" ]]; then
        echo ""
        return 0
    fi

    if [[ "${path}" != /* ]]; then
        path="/app/${path#./}"
    fi
    echo "${path}"
}

DB_PATH="$(sqlite_path_from_url)"
if [[ -n "${DB_PATH}" ]]; then
    DATA_DIR="$(dirname "${DB_PATH}")"
else
    DATA_DIR="/app/data"
fi

UPLOAD_DIR="${UPLOAD_DIR:-/app/uploads}"
REPORTS_DIR="${REPORTS_DIR:-/app/reports}"
BACKUPS_DIR="${BACKUPS_DIR:-/app/backups}"
LOGS_DIR="${LOGS_DIR:-/app/logs}"
STAGING_PATH="${DATA_DIR}/staging_restore.db"
LOCK_PATH="${DATA_DIR}/restart.lock"

mkdir -p "${DATA_DIR}" "${UPLOAD_DIR}" "${REPORTS_DIR}" "${BACKUPS_DIR}" "${LOGS_DIR}"

if [[ -f "${STAGING_PATH}" ]]; then
    if [[ -z "${DB_PATH}" ]]; then
        echo "[entrypoint] Restore staged, but DATABASE_URL is not a file-backed SQLite URL."
        exit 1
    fi

    echo "[entrypoint] Detected staged restore at ${STAGING_PATH}; replacing ${DB_PATH}."
    rm -f "${DB_PATH}-wal" "${DB_PATH}-shm"
    mv "${STAGING_PATH}" "${DB_PATH}"
    rm -f "${LOCK_PATH}"
    echo "[entrypoint] Database restore complete."
elif [[ -f "${LOCK_PATH}" ]]; then
    echo "[entrypoint] Removing stale restart lock at ${LOCK_PATH}; no staged DB was present."
    rm -f "${LOCK_PATH}"
fi

if [[ "${RUN_MIGRATIONS:-true}" == "true" ]]; then
    echo "[entrypoint] Running database migrations..."
    alembic upgrade head
else
    echo "[entrypoint] Skipping migrations because RUN_MIGRATIONS=${RUN_MIGRATIONS:-false}."
fi

echo "[entrypoint] Starting: $*"
exec "$@"
