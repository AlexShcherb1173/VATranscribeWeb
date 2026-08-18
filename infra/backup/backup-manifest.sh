#!/usr/bin/env bash
set -euo pipefail

ARTIFACT_PATH="${1:-}"
OUTPUT_PATH="${2:-}"
[[ -n "${ARTIFACT_PATH}" && -f "${ARTIFACT_PATH}" ]] || { echo "Usage: $0 /path/to/backup.dump[.age] [/path/to/manifest.json]" >&2; exit 2; }
[[ -n "${OUTPUT_PATH}" ]] || OUTPUT_PATH="${ARTIFACT_PATH}.manifest.json"

PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
POSTGRES_DB="${POSTGRES_DB:-vatranscribe}"
BACKUP_TIER="${BACKUP_TIER:-daily}"
BACKUP_RPO_HOURS="${BACKUP_RPO_HOURS:-24}"
BACKUP_RTO_HOURS="${BACKUP_RTO_HOURS:-2}"
BACKUP_RETENTION_DAILY="${BACKUP_RETENTION_DAILY:-14}"
BACKUP_RETENTION_WEEKLY="${BACKUP_RETENTION_WEEKLY:-8}"
BACKUP_RETENTION_MONTHLY="${BACKUP_RETENTION_MONTHLY:-6}"
BACKUP_MANIFEST_VERSION="${BACKUP_MANIFEST_VERSION:-1}"
BACKUP_REMOTE="${BACKUP_REMOTE:-${S3_REMOTE:-}}"
BACKUP_REMOTE_PATH="${BACKUP_REMOTE_PATH:-${S3_BACKUP_PATH:-vatranscribe/postgres}}"
SHA256="$(sha256sum "${ARTIFACT_PATH}" | awk '{print $1}')"
SIZE_BYTES="$(wc -c < "${ARTIFACT_PATH}" | tr -d ' ')"
CREATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
ENCRYPTED="false"
[[ "${ARTIFACT_PATH}" == *.age ]] && ENCRYPTED="true"

cat > "${OUTPUT_PATH}" <<JSON
{
  "manifest_version": "${BACKUP_MANIFEST_VERSION}",
  "created_at_utc": "${CREATED_AT}",
  "project": "${PROJECT_NAME}",
  "database": "${POSTGRES_DB}",
  "tier": "${BACKUP_TIER}",
  "artifact": "$(basename "${ARTIFACT_PATH}")",
  "format": "pg_dump_custom",
  "encrypted_with_age": ${ENCRYPTED},
  "sha256": "${SHA256}",
  "size_bytes": ${SIZE_BYTES},
  "rpo_hours": ${BACKUP_RPO_HOURS},
  "rto_hours": ${BACKUP_RTO_HOURS},
  "retention": {
    "daily": ${BACKUP_RETENTION_DAILY},
    "weekly": ${BACKUP_RETENTION_WEEKLY},
    "monthly": ${BACKUP_RETENTION_MONTHLY}
  },
  "remote": {
    "provider": "rclone",
    "remote": "${BACKUP_REMOTE}",
    "path": "${BACKUP_REMOTE_PATH}"
  }
}
JSON

echo "[OK] Manifest written: ${OUTPUT_PATH}"
