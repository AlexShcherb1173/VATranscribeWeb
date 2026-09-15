#!/usr/bin/env bash
set -euo pipefail

# Validates a backup artifact, checksum, manifest and pg_restore readability.
# DO NOT echo real database URLs, rclone credentials, age identity file contents, or backup keys.

BACKUP_FILE="${1:-}"
AGE_IDENTITY_FILE="${AGE_IDENTITY_FILE:-}"
BACKUP_REQUIRE_ENCRYPTION="${BACKUP_REQUIRE_ENCRYPTION:-true}"
BACKUP_DIR="${BACKUP_DIR:-/opt/vatranscribe/backups}"
APP_ENV="${APP_ENV:-production}"

fail() { echo "[ERROR] $*" >&2; exit 1; }
info() { echo "[INFO] $*" >&2; }
warn() { echo "[WARN] $*" >&2; }

[[ -n "${BACKUP_FILE}" && -f "${BACKUP_FILE}" ]] || fail "Usage: $0 /path/to/backup.dump[.age]"

CHECKSUM_FILE="${BACKUP_FILE}.sha256"
MANIFEST_FILE="${BACKUP_FILE}.manifest.json"
BACKUP_BASENAME="$(basename "${BACKUP_FILE}")"

[[ -f "${CHECKSUM_FILE}" ]] || fail "Missing checksum file: ${CHECKSUM_FILE}"
[[ -f "${MANIFEST_FILE}" ]] || fail "Missing manifest file: ${MANIFEST_FILE}"

if [[ "${APP_ENV}" == "production" || "${BACKUP_REQUIRE_ENCRYPTION}" == "true" ]]; then
  [[ "${BACKUP_FILE}" == *.age ]] || fail "Production backup proof requires encrypted .dump.age artifact"
  grep -q '"encrypted_with_age": true' "${MANIFEST_FILE}" || fail "Manifest must declare encrypted_with_age=true"
fi

grep -q '"format": "pg_dump_custom"' "${MANIFEST_FILE}" || fail "Manifest must declare pg_dump_custom format"
grep -q '"sha256"' "${MANIFEST_FILE}" || fail "Manifest must contain sha256"
grep -q '"rpo_hours": 24' "${MANIFEST_FILE}" || warn "Manifest does not declare expected RPO 24 hours"
grep -q '"rto_hours": 2' "${MANIFEST_FILE}" || warn "Manifest does not declare expected RTO 2 hours"
grep -q '"daily": 14' "${MANIFEST_FILE}" || warn "Manifest does not declare daily retention 14"
grep -q '"weekly": 8' "${MANIFEST_FILE}" || warn "Manifest does not declare weekly retention 8"
grep -q '"monthly": 6' "${MANIFEST_FILE}" || warn "Manifest does not declare monthly retention 6"

EXPECTED_SHA="$(awk '{print $1}' "${CHECKSUM_FILE}")"
grep -q "${EXPECTED_SHA}" "${MANIFEST_FILE}" || fail "Manifest sha256 does not match checksum file"

(cd "$(dirname "${BACKUP_FILE}")" && sha256sum -c "$(basename "${CHECKSUM_FILE}")")

TMP_DUMP=""
cleanup() { [[ -n "${TMP_DUMP}" && -f "${TMP_DUMP}" ]] && rm -f "${TMP_DUMP}"; }
trap cleanup EXIT

if [[ "${BACKUP_FILE}" == *.age ]]; then
  info "Encrypted age backup detected: ${BACKUP_BASENAME}"
  if [[ -n "${AGE_IDENTITY_FILE}" && -f "${AGE_IDENTITY_FILE}" ]]; then
    TMP_DUMP="$(mktemp)"
    age -d -i "${AGE_IDENTITY_FILE}" -o "${TMP_DUMP}" "${BACKUP_FILE}"
    pg_restore --list "${TMP_DUMP}" >/dev/null
    info "age decrypt and pg_restore --list validation passed"
  else
    warn "AGE_IDENTITY_FILE is not set; checksum and manifest verified without decrypt check"
  fi
else
  pg_restore --list "${BACKUP_FILE}" >/dev/null
  info "Plain pg_dump custom artifact pg_restore --list validation passed"
fi

echo "BACKUP_ARTIFACT=${BACKUP_BASENAME}"
echo "BACKUP_SHA256_PREFIX=${EXPECTED_SHA:0:16}"
echo "BACKUP_VALIDATION_RESULT=passed"
