#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE="${1:-}"
AGE_IDENTITY_FILE="${AGE_IDENTITY_FILE:-}"
[[ -n "${BACKUP_FILE}" && -f "${BACKUP_FILE}" ]] || { echo "Usage: $0 /path/to/backup.dump[.age]" >&2; exit 2; }

fail() { echo "[ERROR] $*" >&2; exit 1; }
info() { echo "[INFO] $*" >&2; }

if [[ -f "${BACKUP_FILE}.sha256" ]]; then
  (cd "$(dirname "${BACKUP_FILE}")" && sha256sum -c "$(basename "${BACKUP_FILE}.sha256")")
else
  fail "Missing checksum file: ${BACKUP_FILE}.sha256"
fi

if [[ -f "${BACKUP_FILE}.manifest.json" ]]; then
  grep -q '"sha256"' "${BACKUP_FILE}.manifest.json" || fail "Manifest does not contain sha256"
  grep -q '"format": "pg_dump_custom"' "${BACKUP_FILE}.manifest.json" || fail "Manifest does not declare pg_dump_custom format"
else
  fail "Missing manifest file: ${BACKUP_FILE}.manifest.json"
fi

TMP_DUMP=""
cleanup() { [[ -n "${TMP_DUMP}" && -f "${TMP_DUMP}" ]] && rm -f "${TMP_DUMP}"; }
trap cleanup EXIT

if [[ "${BACKUP_FILE}" == *.age ]]; then
  info "Encrypted age backup detected"
  if [[ -n "${AGE_IDENTITY_FILE}" && -f "${AGE_IDENTITY_FILE}" ]]; then
    TMP_DUMP="$(mktemp)"
    age -d -i "${AGE_IDENTITY_FILE}" -o "${TMP_DUMP}" "${BACKUP_FILE}"
    pg_restore --list "${TMP_DUMP}" >/dev/null
    info "Encrypted backup decrypted and pg_restore --list validation passed"
  else
    info "AGE_IDENTITY_FILE is not set; checksum/manifest verification completed without decrypt drill"
  fi
else
  pg_restore --list "${BACKUP_FILE}" >/dev/null
  info "Plain pg_dump custom backup validation passed"
fi

info "Backup verification completed: ${BACKUP_FILE}"
