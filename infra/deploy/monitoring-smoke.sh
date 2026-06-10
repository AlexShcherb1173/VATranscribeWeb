#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${UPTIME_CHECKS_BASE_URL:-${SMOKE_BASE_URL:-https://vatranscribe.ru}}"
API_BASE_URL="${PUBLIC_API_ORIGIN:-https://api.vatranscribe.ru}"
TIMEOUT="${SMOKE_TIMEOUT_SECONDS:-10}"

curl_check() {
  local url="$1"
  echo "[INFO] Checking ${url}"
  curl --fail --silent --show-error --max-time "${TIMEOUT}" "${url}" >/dev/null
}

curl_check "${BASE_URL}"
curl_check "${API_BASE_URL}/api/v1/health/live"
curl_check "${API_BASE_URL}/api/v1/health/ready"

echo "[OK] Monitoring smoke checks passed"
