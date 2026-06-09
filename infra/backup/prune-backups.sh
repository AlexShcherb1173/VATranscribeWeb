#!/usr/bin/env bash
set -euo pipefail
BACKUP_DIR="${BACKUP_DIR:-/backups/vatranscribe}"
BACKUP_RETENTION_DAILY="${BACKUP_RETENTION_DAILY:-7}"
BACKUP_RETENTION_WEEKLY="${BACKUP_RETENTION_WEEKLY:-4}"
BACKUP_RETENTION_MONTHLY="${BACKUP_RETENTION_MONTHLY:-6}"
mkdir -p "${BACKUP_DIR}/daily" "${BACKUP_DIR}/weekly" "${BACKUP_DIR}/monthly"
prune_tier() {
  local tier="$1"; local keep="$2"; local dir="${BACKUP_DIR}/${tier}"
  find "${dir}" -maxdepth 1 -type f \( -name '*.dump' -o -name '*.dump.age' \) | sort -r | tail -n +$((keep + 1)) | while read -r file; do
    rm -f "${file}" "${file}.sha256"
  done
}
prune_tier daily "${BACKUP_RETENTION_DAILY}"
prune_tier weekly "${BACKUP_RETENTION_WEEKLY}"
prune_tier monthly "${BACKUP_RETENTION_MONTHLY}"
