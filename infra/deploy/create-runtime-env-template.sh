#!/usr/bin/env bash
set -euo pipefail

SOURCE_FILE="${1:-.env.production.example}"
OUTPUT_FILE="${2:-runtime-env.manual.template}"

fail() { echo "[ERROR] $*" >&2; exit 1; }

[[ -f "${SOURCE_FILE}" ]] || fail "Source env template not found: ${SOURCE_FILE}"

umask 077
mkdir -p "$(dirname "${OUTPUT_FILE}")" 2>/dev/null || true

tmp_file="$(mktemp "${OUTPUT_FILE}.XXXXXX")"
trap 'rm -f "${tmp_file}"' EXIT

cat > "${tmp_file}" <<'HEADER'
# VATranscribe runtime environment template.
# Generated for manual secret filling.
# DO NOT COMMIT a filled copy.
# Recommended production path: /opt/vatranscribe/secrets/.env.runtime
# Fill values on the production host or in the chosen secret manager.

HEADER

is_secret_key() {
  local key="$1"
  [[ "${key}" =~ (SECRET|PASSWORD|PRIVATE|TOKEN|API_KEY|WEBHOOK|ENCRYPTION_KEY|DSN|SMTP_PASSWORD|DATABASE_URL|REDIS_URL|CELERY_BROKER_URL|CELERY_RESULT_BACKEND|YOUTUBE_COOKIES_ENCRYPTION_KEY|AGE_IDENTITY_FILE) ]]
}

normalize_value() {
  local key="$1"
  local value="$2"

  case "${key}" in
    APP_ENV) echo "production"; return ;;
    DEBUG|EXPOSE_API_DOCS|BILLING_FAKE_UPGRADE_ENABLED|RATE_LIMIT_REDIS_FAIL_OPEN) echo "false"; return ;;
    COOKIE_SECURE|COOKIE_HTTPONLY|ADMIN_2FA_REQUIRED|PRODUCTION_SECRETS_VALIDATION_REQUIRED|BACKUP_REQUIRE_ENCRYPTION|COOKIE_CONSENT_REQUIRED|VITE_COOKIE_CONSENT_REQUIRED|PUBLIC_COOKIE_CONSENT_REQUIRED|LOG_JSON) echo "true"; return ;;
    SECRET_MANAGER_STRATEGY) echo "runtime-env-file"; return ;;
    RUNTIME_ENV_FILE) echo "/opt/vatranscribe/secrets/.env.runtime"; return ;;
    PAYMENT_PROVIDER|ANALYTICS_PROVIDER) echo "disabled"; return ;;
    RUNTIME_ENV_FILE|CERTBOT_WEBROOT|NGINX_SSL_CERTIFICATE|NGINX_SSL_CERTIFICATE_KEY) echo "${value}"; return ;;
  esac

  if is_secret_key "${key}"; then
    echo "<REQUIRED_SECRET>"
    return
  fi

  if [[ -z "${value}" ]]; then
    echo "<FILL_OR_LEAVE_EMPTY_IF_OPTIONAL>"
    return
  fi

  if [[ "${value}" =~ CHANGE_ME|change-me|example\.com|localhost|127\.0\.0\.1|super-secret|local-dev|placeholder ]]; then
    echo "<REQUIRED_PRODUCTION_VALUE>"
    return
  fi

  echo "${value}"
}

while IFS= read -r line || [[ -n "${line}" ]]; do
  if [[ -z "${line}" ]]; then
    printf '\n' >> "${tmp_file}"
    continue
  fi

  if [[ "${line}" =~ ^[[:space:]]*# ]]; then
    printf '%s\n' "${line}" >> "${tmp_file}"
    continue
  fi

  if [[ "${line}" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
    key="${BASH_REMATCH[1]}"
    value="${BASH_REMATCH[2]}"
    normalized="$(normalize_value "${key}" "${value}")"
    printf '%s=%s\n' "${key}" "${normalized}" >> "${tmp_file}"
  else
    printf '%s\n' "${line}" >> "${tmp_file}"
  fi
done < "${SOURCE_FILE}"

install -m 600 "${tmp_file}" "${OUTPUT_FILE}"
trap - EXIT
rm -f "${tmp_file}"

echo "[OK] Runtime env manual template created: ${OUTPUT_FILE}"
echo "[INFO] Fill it outside Git, then install as /opt/vatranscribe/secrets/.env.runtime"
