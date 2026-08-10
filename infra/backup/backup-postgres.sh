#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-}"
DB_SERVICE="${DB_SERVICE:-db}"
POSTGRES_DB="${POSTGRES_DB:-vatranscribe}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
BACKUP_DIR="${BACKUP_DIR:-/backups/vatranscribe}"
BACKUP_TIER="${BACKUP_TIER:-daily}"
BACKUP_RPO_HOURS="${BACKUP_RPO_HOURS:-24}"
BACKUP_RTO_HOURS="${BACKUP_RTO_HOURS:-2}"
BACKUP_RETENTION_DAILY="${BACKUP_RETENTION_DAILY:-14}"
BACKUP_RETENTION_WEEKLY="${BACKUP_RETENTION_WEEKLY:-8}"
BACKUP_RETENTION_MONTHLY="${BACKUP_RETENTION_MONTHLY:-6}"
BACKUP_REQUIRE_ENCRYPTION="${BACKUP_REQUIRE_ENCRYPTION:-false}"
BACKUP_ENCRYPTION_RECIPIENT="${BACKUP_ENCRYPTION_RECIPIENT:-${AGE_RECIPIENT:-}}"
BACKUP_REMOTE="${BACKUP_REMOTE:-${S3_REMOTE:-}}"
BACKUP_REMOTE_PATH="${BACKUP_REMOTE_PATH:-${S3_BACKUP_PATH:-vatranscribe/postgres}}"
BACKUP_VERIFY_AFTER_CREATE="${BACKUP_VERIFY_AFTER_CREATE:-true}"
BACKUP_MANIFEST_VERSION="${BACKUP_MANIFEST_VERSION:-1}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BASE_NAME="${PROJECT_NAME}_${POSTGRES_DB}_${STAMP}"
WORK_DIR="${BACKUP_DIR}/incoming/${BASE_NAME}"
FINAL_DIR="${BACKUP_DIR}/${BACKUP_TIER}"
DUMP_PATH="${WORK_DIR}/${BASE_NAME}.dump"
ARTIFACT_PATH="${FINAL_DIR}/${BASE_NAME}.dump"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

fail() { echo "[ERROR] $*" >&2; exit 1; }
info() { echo "[INFO] $*" >&2; }
warn() { echo "[WARN] $*" >&2; }

case "${BACKUP_TIER}" in
  daily|weekly|monthly) ;;
  *) fail "BACKUP_TIER must be daily, weekly or monthly" ;;
esac

if [[ "${APP_ENV:-}" == "production" && "${BACKUP_REQUIRE_ENCRYPTION}" != "true" ]]; then
  fail "BACKUP_REQUIRE_ENCRYPTION must be true in production"
fi

if [[ "${BACKUP_REQUIRE_ENCRYPTION}" == "true" && -z "${BACKUP_ENCRYPTION_RECIPIENT}" ]]; then
  fail "BACKUP_ENCRYPTION_RECIPIENT or AGE_RECIPIENT is required when BACKUP_REQUIRE_ENCRYPTION=true"
fi

compose_exec() {
  if [[ -n "${RUNTIME_ENV_FILE}" && -f "${RUNTIME_ENV_FILE}" ]]; then
    # shellcheck disable=SC2086
    docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} "$@"
  else
    # shellcheck disable=SC2086
    docker compose -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} "$@"
  fi
}

mkdir -p "${WORK_DIR}" "${FINAL_DIR}" "${BACKUP_DIR}/daily" "${BACKUP_DIR}/weekly" "${BACKUP_DIR}/monthly" "${BACKUP_DIR}/manifests"

info "Creating PostgreSQL pg_dump custom-format backup: ${BASE_NAME}"
compose_exec exec -T "${DB_SERVICE}" \
  pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --format=custom --no-owner --no-acl > "${DUMP_PATH}"

pg_restore --list "${DUMP_PATH}" >/dev/null
info "Local pg_restore --list validation passed"

if [[ -n "${BACKUP_ENCRYPTION_RECIPIENT}" ]]; then
  info "Encrypting backup with age recipient"
  age -r "${BACKUP_ENCRYPTION_RECIPIENT}" -o "${DUMP_PATH}.age" "${DUMP_PATH}"
  rm -f "${DUMP_PATH}"
  ARTIFACT_PATH="${FINAL_DIR}/${BASE_NAME}.dump.age"
  mv "${DUMP_PATH}.age" "${ARTIFACT_PATH}"
else
  warn "BACKUP_ENCRYPTION_RECIPIENT is empty; storing unencrypted local backup. This is forbidden for production."
  mv "${DUMP_PATH}" "${ARTIFACT_PATH}"
fi

sha256sum "${ARTIFACT_PATH}" > "${ARTIFACT_PATH}.sha256"
"${SCRIPT_DIR}/backup-manifest.sh" "${ARTIFACT_PATH}" "${ARTIFACT_PATH}.manifest.json"
cp "${ARTIFACT_PATH}.manifest.json" "${BACKUP_DIR}/manifests/${BASE_NAME}.manifest.json"
ln -sfn "${ARTIFACT_PATH}" "${FINAL_DIR}/latest.dump${ARTIFACT_PATH##*.dump}"

if [[ "${BACKUP_VERIFY_AFTER_CREATE}" == "true" ]]; then
  "${SCRIPT_DIR}/backup-verify.sh" "${ARTIFACT_PATH}"
fi

if [[ -n "${BACKUP_REMOTE}" ]]; then
  info "Uploading backup and metadata with rclone: ${BACKUP_REMOTE}:${BACKUP_REMOTE_PATH}/${BACKUP_TIER}/"
  rclone copy "${ARTIFACT_PATH}" "${BACKUP_REMOTE}:${BACKUP_REMOTE_PATH}/${BACKUP_TIER}/"
  rclone copy "${ARTIFACT_PATH}.sha256" "${BACKUP_REMOTE}:${BACKUP_REMOTE_PATH}/${BACKUP_TIER}/"
  rclone copy "${ARTIFACT_PATH}.manifest.json" "${BACKUP_REMOTE}:${BACKUP_REMOTE_PATH}/${BACKUP_TIER}/"
else
  warn "BACKUP_REMOTE is empty; remote upload skipped"
fi

rm -rf "${WORK_DIR}"
"${SCRIPT_DIR}/prune-backups.sh"
info "Backup written: ${ARTIFACT_PATH}"
info "Manifest: ${ARTIFACT_PATH}.manifest.json"
