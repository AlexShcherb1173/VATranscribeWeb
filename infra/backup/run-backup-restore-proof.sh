#!/usr/bin/env bash
set -euo pipefail

# P3-05 Backup restore proof orchestration.
# DO NOT echo real secrets, runtime env values, age identities, rclone tokens, or database passwords.

RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
BACKUP_DIR="${BACKUP_DIR:-/opt/vatranscribe/backups}"
BACKUP_TIER="${BACKUP_TIER:-daily}"
BACKUP_REQUIRE_ENCRYPTION="${BACKUP_REQUIRE_ENCRYPTION:-true}"
BACKUP_VERIFY_AFTER_CREATE="${BACKUP_VERIFY_AFTER_CREATE:-true}"
RESTORE_DRILL_DATABASE="${RESTORE_DRILL_DATABASE:-vatranscribe_restore_drill}"
RESTORE_DRILL_REPORT_DIR="${RESTORE_DRILL_REPORT_DIR:-${BACKUP_DIR}/restore-drills}"
BACKUP_PROOF_EVIDENCE_DIR="${BACKUP_PROOF_EVIDENCE_DIR:-${BACKUP_DIR}/evidence}"
BACKUP_PROOF_REQUIRE_REMOTE="${BACKUP_PROOF_REQUIRE_REMOTE:-false}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

fail() { echo "[ERROR] $*" >&2; exit 1; }
info() { echo "[INFO] $*" >&2; }
warn() { echo "[WARN] $*" >&2; }

source_runtime_env() {
  if [[ -f "${RUNTIME_ENV_FILE}" ]]; then
    info "Loading runtime env from ${RUNTIME_ENV_FILE}"
    set -a
    # shellcheck disable=SC1090
    source "${RUNTIME_ENV_FILE}"
    set +a
  else
    warn "Runtime env file not found: ${RUNTIME_ENV_FILE}; using current process environment"
  fi
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

latest_backup_artifact() {
  find "${BACKUP_DIR}/${BACKUP_TIER}" -maxdepth 1 -type f \( -name '*.dump.age' -o -name '*.dump' \) | sort | tail -n 1
}

source_runtime_env

BACKUP_DIR="${BACKUP_DIR:-/opt/vatranscribe/backups}"
BACKUP_TIER="${BACKUP_TIER:-daily}"
BACKUP_REQUIRE_ENCRYPTION="${BACKUP_REQUIRE_ENCRYPTION:-true}"
RESTORE_DRILL_DATABASE="${RESTORE_DRILL_DATABASE:-vatranscribe_restore_drill}"
RESTORE_DRILL_REPORT_DIR="${RESTORE_DRILL_REPORT_DIR:-${BACKUP_DIR}/restore-drills}"
BACKUP_PROOF_EVIDENCE_DIR="${BACKUP_PROOF_EVIDENCE_DIR:-${BACKUP_DIR}/evidence}"

[[ "${BACKUP_TIER}" =~ ^(daily|weekly|monthly)$ ]] || fail "BACKUP_TIER must be daily, weekly or monthly"
[[ "${RESTORE_DRILL_DATABASE}" != "${POSTGRES_DB:-vatranscribe}" ]] || fail "RESTORE_DRILL_DATABASE must not equal POSTGRES_DB"

require_command docker
require_command pg_restore
require_command sha256sum

if [[ "${BACKUP_REQUIRE_ENCRYPTION}" == "true" ]]; then
  require_command age
  [[ -n "${BACKUP_ENCRYPTION_RECIPIENT:-${AGE_RECIPIENT:-}}" ]] || fail "BACKUP_ENCRYPTION_RECIPIENT or AGE_RECIPIENT is required"
  [[ -n "${AGE_IDENTITY_FILE:-}" && -f "${AGE_IDENTITY_FILE:-}" ]] || fail "AGE_IDENTITY_FILE is required for encrypted restore proof"
fi

if [[ "${BACKUP_PROOF_REQUIRE_REMOTE}" == "true" ]]; then
  require_command rclone
  [[ -n "${BACKUP_REMOTE:-${S3_REMOTE:-}}" ]] || fail "BACKUP_REMOTE or S3_REMOTE is required when BACKUP_PROOF_REQUIRE_REMOTE=true"
fi

mkdir -p "${BACKUP_DIR}" "${RESTORE_DRILL_REPORT_DIR}" "${BACKUP_PROOF_EVIDENCE_DIR}"

info "Starting P3-05 backup restore proof"
info "Scope: PostgreSQL pg_dump custom format, age encryption, manifest, checksum, disposable restore drill"

APP_ENV="${APP_ENV:-production}" \
BACKUP_DIR="${BACKUP_DIR}" \
BACKUP_TIER="${BACKUP_TIER}" \
BACKUP_REQUIRE_ENCRYPTION="${BACKUP_REQUIRE_ENCRYPTION}" \
BACKUP_VERIFY_AFTER_CREATE="${BACKUP_VERIFY_AFTER_CREATE}" \
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE}" \
  "${SCRIPT_DIR}/backup-postgres.sh"

BACKUP_FILE="$(latest_backup_artifact)"
[[ -n "${BACKUP_FILE}" && -f "${BACKUP_FILE}" ]] || fail "No backup artifact found after backup run"

info "Validating backup artifact: $(basename "${BACKUP_FILE}")"
APP_ENV="${APP_ENV:-production}" \
BACKUP_REQUIRE_ENCRYPTION="${BACKUP_REQUIRE_ENCRYPTION}" \
AGE_IDENTITY_FILE="${AGE_IDENTITY_FILE:-}" \
  "${SCRIPT_DIR}/validate-backup-artifacts.sh" "${BACKUP_FILE}"

info "Running disposable restore drill"
APP_ENV="${APP_ENV:-production}" \
BACKUP_DIR="${BACKUP_DIR}" \
RESTORE_DRILL_DATABASE="${RESTORE_DRILL_DATABASE}" \
RESTORE_DRILL_REPORT_DIR="${RESTORE_DRILL_REPORT_DIR}" \
AGE_IDENTITY_FILE="${AGE_IDENTITY_FILE:-}" \
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE}" \
  "${SCRIPT_DIR}/restore-drill.sh" "${BACKUP_FILE}"

RESTORE_REPORT="$(find "${RESTORE_DRILL_REPORT_DIR}" -maxdepth 1 -type f -name 'restore-drill-*.md' | sort | tail -n 1)"
[[ -n "${RESTORE_REPORT}" && -f "${RESTORE_REPORT}" ]] || fail "Restore drill report was not found"

EVIDENCE_PATH="${BACKUP_PROOF_EVIDENCE_DIR}/backup-restore-proof-evidence-${STAMP}.md"
"${SCRIPT_DIR}/redact-backup-restore-report.sh" "${RESTORE_REPORT}" "${EVIDENCE_PATH}"

info "P3-05 backup restore proof completed"
info "Sanitized evidence: ${EVIDENCE_PATH}"
info "Do not commit generated evidence or backup artifacts to Git."
