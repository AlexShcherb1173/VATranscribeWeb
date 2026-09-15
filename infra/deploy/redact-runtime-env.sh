#!/usr/bin/env bash
set -euo pipefail

RUNTIME_ENV_FILE="${1:-${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}}"

fail() { echo "[ERROR] $*" >&2; exit 1; }

[[ -f "${RUNTIME_ENV_FILE}" ]] || fail "Runtime env file not found: ${RUNTIME_ENV_FILE}"
[[ -r "${RUNTIME_ENV_FILE}" ]] || fail "Runtime env file is not readable: ${RUNTIME_ENV_FILE}"

is_sensitive_key() {
  local key="$1"
  [[ "${key}" =~ (SECRET|PASSWORD|PRIVATE|TOKEN|API_KEY|WEBHOOK|ENCRYPTION|DSN|DATABASE_URL|REDIS_URL|CELERY_BROKER_URL|CELERY_RESULT_BACKEND|SMTP|PAYMENT|YOUTUBE_COOKIES|AGE_IDENTITY|BACKUP_REMOTE|SENTRY_DSN|COOKIE) ]]
}

redact_value() {
  local key="$1"
  local value="$2"

  if is_sensitive_key "${key}"; then
    if [[ -z "${value}" ]]; then
      echo "<empty>"
    else
      echo "<redacted:set>"
    fi
    return
  fi

  if [[ -z "${value}" ]]; then
    echo "<empty>"
    return
  fi

  if [[ "${value}" =~ CHANGE_ME|change-me|example\.com|localhost|127\.0\.0\.1|super-secret|local-dev|placeholder ]]; then
    echo "<placeholder>"
    return
  fi

  echo "${value}"
}

printf '# VATranscribe runtime secrets redacted evidence\n'
printf '# Generated at: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '# Source: %s\n' "${RUNTIME_ENV_FILE}"
printf '# Values marked <redacted:set> were present but intentionally not printed.\n\n'

key_count=0
sensitive_set_count=0
placeholder_count=0

while IFS= read -r line || [[ -n "${line}" ]]; do
  [[ -z "${line}" || "${line}" =~ ^[[:space:]]*# ]] && continue
  [[ "${line}" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]] || continue

  key="${BASH_REMATCH[1]}"
  value="${BASH_REMATCH[2]}"
  redacted="$(redact_value "${key}" "${value}")"

  key_count=$((key_count + 1))
  if [[ "${redacted}" == "<redacted:set>" ]]; then
    sensitive_set_count=$((sensitive_set_count + 1))
  fi
  if [[ "${redacted}" == "<placeholder>" ]]; then
    placeholder_count=$((placeholder_count + 1))
  fi

  printf '%s=%s\n' "${key}" "${redacted}"
done < "${RUNTIME_ENV_FILE}"

printf '\n# Summary\n'
printf 'KEY_COUNT=%s\n' "${key_count}"
printf 'SENSITIVE_SET_COUNT=%s\n' "${sensitive_set_count}"
printf 'PLACEHOLDER_COUNT=%s\n' "${placeholder_count}"
