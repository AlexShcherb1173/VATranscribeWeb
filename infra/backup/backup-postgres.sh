#!/usr/bin/env bash
set -euo pipefail
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
DB_SERVICE="${DB_SERVICE:-db}"
POSTGRES_DB="${POSTGRES_DB:-vatranscribe}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
BACKUP_DIR="${BACKUP_DIR:-/backups/vatranscribe}"
BACKUP_RETENTION_DAILY="${BACKUP_RETENTION_DAILY:-7}"
BACKUP_RETENTION_WEEKLY="${BACKUP_RETENTION_WEEKLY:-4}"
BACKUP_RETENTION_MONTHLY="${BACKUP_RETENTION_MONTHLY:-6}"
AGE_RECIPIENT="${AGE_RECIPIENT:-}"
S3_REMOTE="${S3_REMOTE:-}"
S3_BACKUP_PATH="${S3_BACKUP_PATH:-vatranscribe/postgres}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BASE_NAME="${PROJECT_NAME}_${POSTGRES_DB}_${STAMP}"
WORK_DIR="${BACKUP_DIR}/incoming/${BASE_NAME}"
FINAL_DIR="${BACKUP_DIR}/daily"
DUMP_PATH="${WORK_DIR}/${BASE_NAME}.dump"
FINAL_PATH="${FINAL_DIR}/${BASE_NAME}.dump"
mkdir -p "${WORK_DIR}" "${FINAL_DIR}" "${BACKUP_DIR}/weekly" "${BACKUP_DIR}/monthly"
printf '[INFO] Creating pg_dump backup %s\n' "${BASE_NAME}"
# shellcheck disable=SC2086
docker compose -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} exec -T "${DB_SERVICE}" \
  pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --format=custom --no-owner --no-acl > "${DUMP_PATH}"
sha256sum "${DUMP_PATH}" > "${WORK_DIR}/manifest.sha256"
if [[ -n "${AGE_RECIPIENT}" ]]; then
  age -r "${AGE_RECIPIENT}" -o "${DUMP_PATH}.age" "${DUMP_PATH}"
  rm -f "${DUMP_PATH}"
  sha256sum "${DUMP_PATH}.age" > "${WORK_DIR}/manifest.sha256"
  FINAL_PATH="${FINAL_PATH}.age"
  mv "${DUMP_PATH}.age" "${FINAL_PATH}"
else
  printf '[WARN] AGE_RECIPIENT is empty; storing unencrypted local backup\n'
  mv "${DUMP_PATH}" "${FINAL_PATH}"
fi
mv "${WORK_DIR}/manifest.sha256" "${FINAL_PATH}.sha256"
rmdir "${WORK_DIR}" 2>/dev/null || true
printf '[INFO] Backup written: %s\n' "${FINAL_PATH}"
if [[ -n "${S3_REMOTE}" ]]; then
  rclone copy "${FINAL_PATH}" "${S3_REMOTE}:${S3_BACKUP_PATH}/daily/"
  rclone copy "${FINAL_PATH}.sha256" "${S3_REMOTE}:${S3_BACKUP_PATH}/daily/"
fi
"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/prune-backups.sh"
