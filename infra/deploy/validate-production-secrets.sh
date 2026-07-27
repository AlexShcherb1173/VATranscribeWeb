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
require_bool_value BILLING_FAKE_UPGRADE_ENABLED false
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

require_non_placeholder ROOT_DOMAIN
require_non_placeholder MARKETING_DOMAIN
require_non_placeholder APP_DOMAIN
require_non_placeholder API_DOMAIN
require_non_placeholder ADMIN_DOMAIN
require_non_placeholder CERTBOT_DOMAINS
require_non_placeholder CERTBOT_PRIMARY_DOMAIN
require_non_placeholder CERTBOT_EMAIL
require_non_placeholder CERTBOT_WEBROOT
require_present CDN_PROVIDER
require_bool_value CDN_API_ENABLED false
require_bool_value HSTS_PRELOAD_ENABLED false

if [[ -n "${PRODUCTION_HOST_PUBLIC_IP:-}" ]]; then
  [[ "${PRODUCTION_HOST_PUBLIC_IP}" != *"CHANGE_ME"* ]] || fail "PRODUCTION_HOST_PUBLIC_IP contains a placeholder value"
fi

for domain_name in ROOT_DOMAIN MARKETING_DOMAIN APP_DOMAIN API_DOMAIN ADMIN_DOMAIN; do
  value="${!domain_name}"
  [[ "${value}" != *"http://"* && "${value}" != *"https://"* ]] || fail "${domain_name} must contain a hostname, not a URL"
  [[ "${value}" != *"localhost"* && "${value}" != *"127.0.0.1"* ]] || fail "${domain_name} must not use localhost"
done


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
require_present BACKUP_RPO_HOURS
require_present BACKUP_RTO_HOURS
require_present BACKUP_RETENTION_DAILY
require_present BACKUP_RETENTION_WEEKLY
require_present BACKUP_RETENTION_MONTHLY
require_present RESTORE_DRILL_DATABASE
[[ "${RESTORE_DRILL_DATABASE}" != "${POSTGRES_DB:-vatranscribe}" ]] || fail "RESTORE_DRILL_DATABASE must not equal POSTGRES_DB"
[[ "${BACKUP_RETENTION_DAILY}" -ge 14 ]] || fail "BACKUP_RETENTION_DAILY must be at least 14"
[[ "${BACKUP_RETENTION_WEEKLY}" -ge 8 ]] || fail "BACKUP_RETENTION_WEEKLY must be at least 8"
[[ "${BACKUP_RETENTION_MONTHLY}" -ge 6 ]] || fail "BACKUP_RETENTION_MONTHLY must be at least 6"
[[ "${BACKUP_RPO_HOURS}" -le 24 ]] || fail "BACKUP_RPO_HOURS must be 24 or less"
[[ "${BACKUP_RTO_HOURS}" -le 2 ]] || fail "BACKUP_RTO_HOURS must be 2 or less"
require_bool_value BACKUP_REQUIRE_ENCRYPTION true

if [[ "${REQUIRE_BACKUP_ENCRYPTION:-true}" == "true" ]]; then
  if [[ -z "${BACKUP_ENCRYPTION_RECIPIENT:-${AGE_RECIPIENT:-}}" ]]; then
    fail "BACKUP_ENCRYPTION_RECIPIENT or AGE_RECIPIENT is required"
  fi
fi


require_bool_value COOKIE_CONSENT_REQUIRED true
require_non_placeholder COOKIE_CONSENT_VERSION
require_present ANALYTICS_PROVIDER
case "${ANALYTICS_PROVIDER}" in
  disabled|yandex|ga4|both|posthog|provider-neutral) ;;
  *) fail "ANALYTICS_PROVIDER has unsupported value: ${ANALYTICS_PROVIDER}" ;;
esac

if [[ "${ANALYTICS_PROVIDER}" == "yandex" || "${ANALYTICS_PROVIDER}" == "both" ]]; then
  require_non_placeholder YANDEX_METRIKA_ID
fi
if [[ "${ANALYTICS_PROVIDER}" == "ga4" || "${ANALYTICS_PROVIDER}" == "both" ]]; then
  require_non_placeholder GA4_MEASUREMENT_ID
fi
if [[ "${ANALYTICS_PROVIDER}" == "posthog" ]]; then
  require_secret_non_placeholder POSTHOG_API_KEY
fi
if [[ "${ANALYTICS_PROVIDER}" != "disabled" && "${ANALYTICS_PROVIDER}" != "provider-neutral" ]]; then
  require_bool_value LEGAL_ANALYTICS_COOKIES_ENABLED true
fi
require_bool_value VITE_COOKIE_CONSENT_REQUIRED true
require_non_placeholder VITE_COOKIE_CONSENT_VERSION
require_bool_value PUBLIC_COOKIE_CONSENT_REQUIRED true
require_non_placeholder PUBLIC_COOKIE_CONSENT_VERSION
require_present CORE_WEB_VITALS_ENABLED
require_present CORE_WEB_VITALS_LCP_TARGET_MS
require_present CORE_WEB_VITALS_INP_TARGET_MS
require_present CORE_WEB_VITALS_CLS_TARGET

optional_secret_if_set SENTRY_DSN
optional_secret_if_set SMTP_PASSWORD
optional_secret_if_set PAYMENT_WEBHOOK_SECRET
optional_secret_if_set PAYMENT_API_KEY
optional_secret_if_set BACKUP_REMOTE
optional_secret_if_set BACKUP_REMOTE_PATH

require_present PAYMENT_PROVIDER
case "${PAYMENT_PROVIDER}" in
  disabled|yookassa|cloudpayments|stripe|robokassa) ;;
  *) fail "PAYMENT_PROVIDER has unsupported value: ${PAYMENT_PROVIDER}" ;;
esac

if [[ "${PAYMENT_PROVIDER:-disabled}" == "disabled" ]]; then
  if [[ "${BILLING_PAID_PLANS_ENABLED:-false}" == "true" ]]; then
    fail "BILLING_PAID_PLANS_ENABLED cannot be true when PAYMENT_PROVIDER=disabled"
  fi
else
  require_bool_value BILLING_PAID_PLANS_ENABLED true
  require_secret_non_placeholder PAYMENT_WEBHOOK_SECRET
  require_secret_non_placeholder PAYMENT_API_KEY
  require_non_placeholder PAYMENT_WEBHOOK_SIGNATURE_HEADER
fi


require_present MONITORING_REQUIRED
if [[ "${MONITORING_REQUIRED,,}" == "true" ]]; then
  require_bool_value MONITORING_RELEASE_CHECKLIST_ACK true
  require_non_placeholder UPTIME_PROVIDER
  [[ "${UPTIME_PROVIDER}" != "disabled" ]] || fail "UPTIME_PROVIDER must not be disabled when MONITORING_REQUIRED=true"
  require_non_placeholder UPTIME_ALERT_CHANNELS
  require_non_placeholder APM_PROVIDER
  [[ "${APM_PROVIDER}" != "disabled" ]] || fail "APM_PROVIDER must not be disabled when MONITORING_REQUIRED=true"
  require_present SENTRY_REQUIRED
  if [[ "${SENTRY_REQUIRED,,}" == "true" || "${APM_PROVIDER}" == "sentry" ]]; then
    require_secret_non_placeholder SENTRY_DSN
  fi
  require_non_placeholder CENTRAL_LOGGING_PROVIDER
  [[ "${CENTRAL_LOGGING_PROVIDER}" != "disabled" ]] || fail "CENTRAL_LOGGING_PROVIDER must not be disabled when MONITORING_REQUIRED=true"
fi

require_present LOG_JSON
require_bool_value LOG_JSON true
require_non_placeholder LOG_LEVEL
require_present LOG_RETENTION_DAYS
require_present LOKI_RETENTION_DAYS
require_present NGINX_ACCESS_LOG_RETENTION_DAYS
require_present NGINX_ERROR_LOG_RETENTION_DAYS
require_non_placeholder REQUEST_ID_HEADER

info "Production secret validation passed for ${RUNTIME_ENV_FILE}"
