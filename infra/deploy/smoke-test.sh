#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${SMOKE_BASE_URL:-http://127.0.0.1}"
API_PREFIX="${API_PREFIX:-/api/v1}"

# Keep the default literal health paths visible for static production checks.
DEFAULT_LIVE_PATH="/api/v1/health/live"
DEFAULT_READY_PATH="/api/v1/health/ready"
LIVE_PATH="${SMOKE_LIVE_PATH:-${API_PREFIX}/health/live}"
READY_PATH="${SMOKE_READY_PATH:-${API_PREFIX}/health/ready}"

curl_check() {
  local url="$1"
  echo "[INFO] Checking ${url}"
  curl --fail --silent --show-error --max-time "${SMOKE_TIMEOUT_SECONDS:-10}" "$url" >/dev/null
}

curl_check "${BASE_URL}${LIVE_PATH}"
curl_check "${BASE_URL}${READY_PATH}"

echo "[OK] Smoke tests passed"
