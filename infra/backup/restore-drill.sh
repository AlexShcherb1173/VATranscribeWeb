#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-}"
DB_SERVICE="${DB_SERVICE:-db}"
POSTGRES_DB="${POSTGRES_DB:-vatranscribe}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
RESTORE_DRILL_ADMIN_USER="${RESTORE_DRILL_ADMIN_USER:-postgres}"
BACKUP_DIR="${BACKUP_DIR:-/backups/vatranscribe}"
RESTORE_DRILL_DATABASE="${RESTORE_DRILL_DATABASE:-vatranscribe_restore_drill}"
RESTORE_DRILL_KEEP_DB="${RESTORE_DRILL_KEEP_DB:-false}"
RESTORE_DRILL_REPORT_DIR="${RESTORE_DRILL_REPORT_DIR:-${BACKUP_DIR}/restore-drills}"
RESTORE_DRILL_EXPECT_ALEMBIC="${RESTORE_DRILL_EXPECT_ALEMBIC:-true}"
CRITICAL_RESTORE_TABLES="${CRITICAL_RESTORE_TABLES:-alembic_version users jobs plans}"
AGE_IDENTITY_FILE="${AGE_IDENTITY_FILE:-}"
BACKUP_FILE="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT_PATH="${RESTORE_DRILL_REPORT_DIR}/restore-drill-${STAMP}.md"

fail() { echo "[ERROR] $*" >&2; exit 1; }
info() { echo "[INFO] $*" >&2; }

if [[ -z "${BACKUP_FILE}" ]]; then
  BACKUP_FILE="$(find "${BACKUP_DIR}/daily" -maxdepth 1 -type f \( -name '*.dump.age' -o -name '*.dump' \) | sort | tail -n 1 || true)"
fi

[[ -n "${BACKUP_FILE}" && -f "${BACKUP_FILE}" ]] || fail "Usage: $0 /path/to/backup.dump[.age] or provide latest daily backup"
[[ "${RESTORE_DRILL_DATABASE}" != "${POSTGRES_DB}" ]] || fail "RESTORE_DRILL_DATABASE must not equal production POSTGRES_DB"
[[ "${RESTORE_DRILL_DATABASE}" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || fail "RESTORE_DRILL_DATABASE contains unsafe characters"
[[ "${POSTGRES_USER}" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || fail "POSTGRES_USER contains unsafe characters"
[[ "${RESTORE_DRILL_ADMIN_USER}" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || fail "RESTORE_DRILL_ADMIN_USER contains unsafe characters"

compose_exec() {
  if [[ -n "${RUNTIME_ENV_FILE}" && -f "${RUNTIME_ENV_FILE}" ]]; then
    # shellcheck disable=SC2086
    docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} "$@"
  else
    # shellcheck disable=SC2086
    docker compose -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} "$@"
  fi
}

mkdir -p "${RESTORE_DRILL_REPORT_DIR}"
"${SCRIPT_DIR}/backup-verify.sh" "${BACKUP_FILE}"

TMP_DUMP="${BACKUP_FILE}"
cleanup() {
  if [[ "${TMP_DUMP}" != "${BACKUP_FILE}" && -f "${TMP_DUMP}" ]]; then
    rm -f "${TMP_DUMP}"
  fi
}
trap cleanup EXIT

if [[ "${BACKUP_FILE}" == *.age ]]; then
  [[ -n "${AGE_IDENTITY_FILE}" && -f "${AGE_IDENTITY_FILE}" ]] || fail "AGE_IDENTITY_FILE is required for encrypted restore drill"
  TMP_DUMP="$(mktemp)"
  age -d -i "${AGE_IDENTITY_FILE}" -o "${TMP_DUMP}" "${BACKUP_FILE}"
fi

pg_restore --list "${TMP_DUMP}" >/dev/null

info "Creating disposable restore database: ${RESTORE_DRILL_DATABASE}"
compose_exec exec -T "${DB_SERVICE}" psql -U "${RESTORE_DRILL_ADMIN_USER}" -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${RESTORE_DRILL_DATABASE}';
DROP DATABASE IF EXISTS ${RESTORE_DRILL_DATABASE};
CREATE DATABASE ${RESTORE_DRILL_DATABASE} OWNER ${POSTGRES_USER};
SQL

info "Restoring backup into disposable database"
compose_exec exec -T "${DB_SERVICE}" \
  pg_restore -U "${POSTGRES_USER}" -d "${RESTORE_DRILL_DATABASE}" --clean --if-exists --no-owner --no-acl < "${TMP_DUMP}"

info "Verifying alembic_version and critical table availability"
if [[ "${RESTORE_DRILL_EXPECT_ALEMBIC}" == "true" ]]; then
  compose_exec exec -T "${DB_SERVICE}" \
    psql -U "${POSTGRES_USER}" -d "${RESTORE_DRILL_DATABASE}" -v ON_ERROR_STOP=1 \
    -c "SELECT version_num FROM alembic_version LIMIT 1;"
fi

for table_name in ${CRITICAL_RESTORE_TABLES}; do
  compose_exec exec -T "${DB_SERVICE}" \
    psql -U "${POSTGRES_USER}" -d "${RESTORE_DRILL_DATABASE}" -v ON_ERROR_STOP=1 \
    -c "SELECT '${table_name}' AS table_name, to_regclass('public.${table_name}') AS regclass;"
done

ROW_COUNT_OUTPUT="$(compose_exec exec -T "${DB_SERVICE}" psql -U "${POSTGRES_USER}" -d "${RESTORE_DRILL_DATABASE}" -v ON_ERROR_STOP=1 -At <<'SQL'
SELECT 'users=' || COUNT(*) FROM users;
SELECT 'jobs=' || COUNT(*) FROM jobs;
SQL
)"

"${SCRIPT_DIR}/restore-drill-report.sh" "${REPORT_PATH}" "${BACKUP_FILE}" "${RESTORE_DRILL_DATABASE}" "passed" "${ROW_COUNT_OUTPUT}"

if [[ "${RESTORE_DRILL_KEEP_DB}" != "true" ]]; then
  info "Dropping disposable restore drill database"
  compose_exec exec -T "${DB_SERVICE}" psql -U "${RESTORE_DRILL_ADMIN_USER}" -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${RESTORE_DRILL_DATABASE}';
DROP DATABASE IF EXISTS ${RESTORE_DRILL_DATABASE};
SQL
fi

info "Restore drill completed. Report: ${REPORT_PATH}"
