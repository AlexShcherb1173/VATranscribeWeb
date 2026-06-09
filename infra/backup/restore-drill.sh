#!/usr/bin/env bash
set -euo pipefail
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
DB_SERVICE="${DB_SERVICE:-db}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
RESTORE_DB="${RESTORE_DB:-vatranscribe_restore_drill}"
AGE_IDENTITY_FILE="${AGE_IDENTITY_FILE:-}"
BACKUP_FILE="${1:-}"
if [[ -z "${BACKUP_FILE}" || ! -f "${BACKUP_FILE}" ]]; then echo "Usage: $0 /path/to/backup.dump[.age]" >&2; exit 2; fi
TMP_DUMP="${BACKUP_FILE}"
if [[ "${BACKUP_FILE}" == *.age ]]; then
  [[ -n "${AGE_IDENTITY_FILE}" ]] || { echo "AGE_IDENTITY_FILE is required" >&2; exit 2; }
  TMP_DUMP="$(mktemp)"; age -d -i "${AGE_IDENTITY_FILE}" -o "${TMP_DUMP}" "${BACKUP_FILE}"
fi
# shellcheck disable=SC2086
docker compose -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} exec -T "${DB_SERVICE}" psql -U "${POSTGRES_USER}" -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${RESTORE_DB}';
DROP DATABASE IF EXISTS ${RESTORE_DB};
CREATE DATABASE ${RESTORE_DB};
SQL
# shellcheck disable=SC2086
docker compose -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} exec -T "${DB_SERVICE}" \
  pg_restore -U "${POSTGRES_USER}" -d "${RESTORE_DB}" --clean --if-exists --no-owner --no-acl < "${TMP_DUMP}"
# shellcheck disable=SC2086
docker compose -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} exec -T "${DB_SERVICE}" \
  psql -U "${POSTGRES_USER}" -d "${RESTORE_DB}" -v ON_ERROR_STOP=1 -c "SELECT current_database(), now();"
[[ "${TMP_DUMP}" == "${BACKUP_FILE}" ]] || rm -f "${TMP_DUMP}"
printf '[OK] Restore drill completed for %s\n' "${RESTORE_DB}"
