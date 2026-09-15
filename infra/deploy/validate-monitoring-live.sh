#!/usr/bin/env bash
set -euo pipefail

# P3-04 live uptime validation for VATranscribeWeb.
# Do not print secrets. This script reads only public URLs and non-secret flags.

RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
SMOKE_TIMEOUT_SECONDS="${SMOKE_TIMEOUT_SECONDS:-10}"
CHECK_ADMIN_DOMAIN="${CHECK_ADMIN_DOMAIN:-false}"

if [[ -f "${RUNTIME_ENV_FILE}" ]]; then
  set -a
  # shellcheck source=/dev/null
  . "${RUNTIME_ENV_FILE}"
  set +a
fi

MARKETING_URL="${PUBLIC_MARKETING_ORIGIN:-https://vatranscribe.ru}"
APP_URL="${PUBLIC_APP_ORIGIN:-https://app.vatranscribe.ru}"
API_URL="${PUBLIC_API_ORIGIN:-https://api.vatranscribe.ru}"
ADMIN_URL="${PUBLIC_ADMIN_ORIGIN:-https://admin.vatranscribe.ru}"

curl_check() {
  local name="$1"
  local url="$2"
  echo "[INFO] ${name}: ${url}"
  local status
  status="$(curl --silent --show-error --location --max-time "${SMOKE_TIMEOUT_SECONDS}" --output /dev/null --write-out '%{http_code}' "${url}")"
  case "${status}" in
    200|204|301|302|307|308)
      echo "[OK] ${name}: HTTP ${status}"
      ;;
    *)
      echo "[FAIL] ${name}: HTTP ${status}" >&2
      return 1
      ;;
  esac
}

curl_check "marketing" "${MARKETING_URL%/}/"
curl_check "app" "${APP_URL%/}/app/"
curl_check "api-live" "${API_URL%/}/api/v1/health/live"
curl_check "api-ready" "${API_URL%/}/api/v1/health/ready"

if [[ "${CHECK_ADMIN_DOMAIN}" == "true" ]]; then
  curl_check "admin" "${ADMIN_URL%/}/"
else
  echo "[INFO] admin domain check skipped. Set CHECK_ADMIN_DOMAIN=true to enable it."
fi

echo "[INFO] UPTIME_PROVIDER=${UPTIME_PROVIDER:-unset}"
echo "[INFO] UPTIME_ALERT_CHANNELS=${UPTIME_ALERT_CHANNELS:-unset}"
echo "[INFO] MONITORING_REQUIRED=${MONITORING_REQUIRED:-unset}"
echo "[OK] P3-04 monitoring live checks passed"
