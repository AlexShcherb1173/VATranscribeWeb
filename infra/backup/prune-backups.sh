#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/vatranscribe}"
BACKUP_RETENTION_DAILY="${BACKUP_RETENTION_DAILY:-14}"
BACKUP_RETENTION_WEEKLY="${BACKUP_RETENTION_WEEKLY:-8}"
BACKUP_RETENTION_MONTHLY="${BACKUP_RETENTION_MONTHLY:-6}"
BACKUP_RETENTION_PRUNE_REMOTE="${BACKUP_RETENTION_PRUNE_REMOTE:-false}"
BACKUP_REMOTE="${BACKUP_REMOTE:-${S3_REMOTE:-}}"
BACKUP_REMOTE_PATH="${BACKUP_REMOTE_PATH:-${S3_BACKUP_PATH:-vatranscribe/postgres}}"

mkdir -p "${BACKUP_DIR}/daily" "${BACKUP_DIR}/weekly" "${BACKUP_DIR}/monthly" "${BACKUP_DIR}/manifests"

prune_tier() {
  local tier="$1"
  local keep="$2"
  local dir="${BACKUP_DIR}/${tier}"
  find "${dir}" -maxdepth 1 -type f \( -name '*.dump' -o -name '*.dump.age' \) | sort -r | tail -n +$((keep + 1)) | while read -r file; do
    rm -f "${file}" "${file}.sha256" "${file}.manifest.json"
  done
}

prune_tier daily "${BACKUP_RETENTION_DAILY}"
prune_tier weekly "${BACKUP_RETENTION_WEEKLY}"
prune_tier monthly "${BACKUP_RETENTION_MONTHLY}"

if [[ "${BACKUP_RETENTION_PRUNE_REMOTE}" == "true" && -n "${BACKUP_REMOTE}" ]]; then
  echo "[INFO] Remote pruning must be configured per provider lifecycle policy: ${BACKUP_REMOTE}:${BACKUP_REMOTE_PATH}"
fi

echo "[OK] Backup retention pruning completed"
