#!/usr/bin/env bash
set -euo pipefail

EVIDENCE_FILE="${1:-}"

if [[ -z "${EVIDENCE_FILE}" || ! -f "${EVIDENCE_FILE}" ]]; then
  echo "Usage: $0 <redacted-production-rehearsal-evidence-file>" >&2
  exit 2
fi

echo "[P3-08] Validating production rehearsal evidence: ${EVIDENCE_FILE}"
echo "[P3-08] DO NOT validate or commit raw evidence containing secrets. Use only redacted evidence."

require_marker() {
  local marker="$1"
  if ! grep -Fq "${marker}" "${EVIDENCE_FILE}"; then
    echo "[FAIL] Missing evidence marker: ${marker}" >&2
    exit 1
  fi
  echo "[OK] ${marker}"
}

forbid_marker() {
  local marker="$1"
  if grep -Fq "${marker}" "${EVIDENCE_FILE}"; then
    echo "[FAIL] Forbidden marker found in redacted evidence: ${marker}" >&2
    exit 1
  fi
}

require_marker "P3_STAGE=P3-08 Production rehearsal"
require_marker "RUNTIME_ENV_FILE=<redacted>"
require_marker "SCRIPT_SYNTAX_RESULT=PASS"
require_marker "RUNTIME_SECRETS_RESULT=PASS"
require_marker "COMPOSE_CONFIG_RESULT=PASS"
require_marker "STAGING_DEPLOY"
require_marker "MIGRATIONS"
require_marker "SMOKE_RESULT=PASS"
require_marker "ROLLBACK_TIMING"
require_marker "BACKUP_RESTORE"
require_marker "AUTH_FILES_JOBS_BILLING_COOKIE_ANALYTICS_RESULT=PASS"
require_marker "AUTH_CHECK_RESULT"
require_marker "FILES_CHECK_RESULT"
require_marker "JOBS_CHECK_RESULT"
require_marker "BILLING_CHECK_RESULT"
require_marker "COOKIE_CHECK_RESULT"
require_marker "ANALYTICS_CHECK_RESULT"
require_marker "PRODUCTION_REHEARSAL_RESULT"
require_marker "GO_NO_GO"

# Release may be blocked if any live step failed. This validator requires explicit decision.
if grep -Fq "GO_NO_GO=NO-GO" "${EVIDENCE_FILE}"; then
  echo "[FAIL] Production rehearsal evidence contains GO_NO_GO=NO-GO" >&2
  exit 1
fi

forbid_marker "super-secret-key-change-me"
forbid_marker "postgres:postgres@"
forbid_marker "DATABASE_URL=postgresql"
forbid_marker "POSTGRES_PASSWORD="
forbid_marker "SECRET_KEY="
forbid_marker "SENTRY_DSN=http"
forbid_marker "PAYMENT_API_KEY="
forbid_marker "PAYMENT_WEBHOOK_SECRET="
forbid_marker "TELEGRAM_ALERT_BOT_TOKEN="
forbid_marker "SMTP_PASSWORD="
forbid_marker "YOUTUBE_COOKIES_ENCRYPTION_KEY="

echo "[OK] Production rehearsal evidence validation passed"
