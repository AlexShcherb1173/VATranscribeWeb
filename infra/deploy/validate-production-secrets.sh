#!/usr/bin/env bash
set -euo pipefail

RUNTIME_ENV_FILE="${1:-${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}}"

fail() { echo "[ERROR] $*" >&2; exit 1; }
warn() { echo "[WARN] $*" >&2; }
info() { echo "[INFO] $*" >&2; }

[[ -f "${RUNTIME_ENV_FILE}" ]] || fail "Runtime env file not found: ${RUNTIME_ENV_FILE}"
[[ -r "${RUNTIME_ENV_FILE}" ]] || fail "Runtime env file is not readable: ${RUNTIME_ENV_FILE}"

# shellcheck disable=SC1090
set -a
source "${RUNTIME_ENV_FILE}"
set +a

placeholder_re='(^$|CHANGE_ME|change-me|changeme|replace-me|replace_me|TODO|TBD|example\.com|example\.org|localhost|super-secret|local-dev|placeholder)'
secret_placeholder_re='(^$|CHANGE_ME|change-me|changeme|replace-me|replace_me|TODO|TBD|example\.com|example\.org|super-secret|local-dev|placeholder)'

require_present() {
  local name="$1"
  local value="${!name-}"
  [[ -n "${value}" ]] || fail "${name} is required in production runtime env"
}

require_non_placeholder() {
  local name="$1"
  require_present "$name"
  local value="${!name}"
  if [[ "${value}" =~ ${placeholder_re} ]]; then
    fail "${name} contains a placeholder/dev value"
  fi
}

require_secret_non_placeholder() {
  local name="$1"
  require_present "$name"
  local value="${!name}"
  if [[ "${value}" =~ ${secret_placeholder_re} ]]; then
    fail "${name} contains a placeholder/dev secret"
  fi
}

require_bool_value() {
  local name="$1" expected="$2"
  require_present "$name"
  local value="${!name}"
  [[ "${value,,}" == "${expected}" ]] || fail "${name} must be ${expected} in production"
}

optional_secret_if_set() {
  local name="$1"
  local value="${!name-}"
  if [[ -n "${value}" && "${value}" =~ ${secret_placeholder_re} ]]; then
    fail "${name} is set but contains a placeholder/dev value"
  fi
}

require_present APP_ENV
[[ "${APP_ENV}" == "production" ]] || fail "APP_ENV must be production"
require_bool_value DEBUG false
require_bool_value EXPOSE_API_DOCS false
require_bool_value COOKIE_SECURE true
require_bool_value COOKIE_HTTPONLY true
require_bool_value ADMIN_2FA_REQUIRED true
require_bool_value RATE_LIMIT_REDIS_FAIL_OPEN false
require_bool_value PRODUCTION_SECRETS_VALIDATION_REQUIRED true

require_non_placeholder SECRET_MANAGER_STRATEGY
case "${SECRET_MANAGER_STRATEGY}" in
  runtime-env-file|github-environments|yandex-lockbox|doppler|hashicorp-vault|onepassword-cli|docker-secrets) ;;
  *) fail "SECRET_MANAGER_STRATEGY must use a production strategy, not '${SECRET_MANAGER_STRATEGY}'" ;;
esac

require_non_placeholder RUNTIME_ENV_FILE
[[ "${RUNTIME_ENV_FILE}" == "${RUNTIME_ENV_FILE:-}" ]] || true

require_secret_non_placeholder SECRET_KEY
[[ "${#SECRET_KEY}" -ge 32 ]] || fail "SECRET_KEY must be at least 32 characters"

require_secret_non_placeholder DATABASE_URL
[[ "${DATABASE_URL,,}" != *"postgres:postgres"* ]] || fail "DATABASE_URL must not use postgres:postgres"
require_secret_non_placeholder POSTGRES_PASSWORD
require_non_placeholder REDIS_URL
require_non_placeholder CELERY_BROKER_URL
require_non_placeholder CELERY_RESULT_BACKEND
require_non_placeholder RATE_LIMIT_BACKEND
[[ "${RATE_LIMIT_BACKEND}" == "redis" ]] || fail "RATE_LIMIT_BACKEND must be redis"

require_non_placeholder CORS_ORIGINS
require_non_placeholder PUBLIC_MARKETING_ORIGIN
require_non_placeholder PUBLIC_APP_ORIGIN
require_non_placeholder PUBLIC_API_ORIGIN
require_non_placeholder PUBLIC_ADMIN_ORIGIN
require_non_placeholder VITE_API_BASE_URL

for origin_name in CORS_ORIGINS PUBLIC_MARKETING_ORIGIN PUBLIC_APP_ORIGIN PUBLIC_API_ORIGIN PUBLIC_ADMIN_ORIGIN VITE_API_BASE_URL; do
  value="${!origin_name}"
  [[ "${value}" == *"https://"* ]] || fail "${origin_name} must use https in production"
  [[ "${value}" != *"localhost"* && "${value}" != *"127.0.0.1"* ]] || fail "${origin_name} must not use localhost"
done

require_secret_non_placeholder YOUTUBE_COOKIES_ENCRYPTION_KEY
[[ "${#YOUTUBE_COOKIES_ENCRYPTION_KEY}" -ge 32 ]] || fail "YOUTUBE_COOKIES_ENCRYPTION_KEY must be high entropy"

require_non_placeholder LEGAL_OPERATOR_NAME
require_non_placeholder LEGAL_CONTACT_EMAIL
require_non_placeholder PRIVACY_CONTACT_EMAIL
require_non_placeholder SUPPORT_EMAIL
require_non_placeholder ADMIN_2FA_ISSUER
require_non_placeholder TRUSTED_PROXY_CIDRS

require_non_placeholder BACKUP_DIR
if [[ "${REQUIRE_BACKUP_ENCRYPTION:-true}" == "true" ]]; then
  if [[ -z "${BACKUP_ENCRYPTION_RECIPIENT:-${AGE_RECIPIENT:-}}" ]]; then
    fail "BACKUP_ENCRYPTION_RECIPIENT or AGE_RECIPIENT is required"
  fi
fi

optional_secret_if_set SENTRY_DSN
optional_secret_if_set SMTP_PASSWORD
optional_secret_if_set PAYMENT_WEBHOOK_SECRET
optional_secret_if_set PAYMENT_API_KEY
optional_secret_if_set BACKUP_REMOTE
optional_secret_if_set BACKUP_REMOTE_PATH

if [[ "${PAYMENT_PROVIDER:-disabled}" != "disabled" ]]; then
  require_secret_non_placeholder PAYMENT_WEBHOOK_SECRET
  require_secret_non_placeholder PAYMENT_API_KEY
fi

info "Production secret validation passed for ${RUNTIME_ENV_FILE}"
