#!/usr/bin/env bash
set -euo pipefail

fail() { echo "[ERROR] $*" >&2; exit 1; }
info() { echo "[INFO] $*" >&2; }
ok() { echo "[OK] $*"; }

RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
if [[ -f "${RUNTIME_ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  set -a; source "${RUNTIME_ENV_FILE}"; set +a
fi

require_tool() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is required"
}
require_tool curl

CDN_PROVIDER="${CDN_PROVIDER:-provider-neutral}"
CDN_API_ENABLED="${CDN_API_ENABLED:-false}"
CDN_MARKETING_STATIC_ENABLED="${CDN_MARKETING_STATIC_ENABLED:-true}"
CDN_APP_STATIC_ENABLED="${CDN_APP_STATIC_ENABLED:-true}"
CDN_HTML_CACHE_POLICY="${CDN_HTML_CACHE_POLICY:-no-cache}"
CDN_ASSET_CACHE_SECONDS="${CDN_ASSET_CACHE_SECONDS:-31536000}"
MARKETING_DOMAIN="${MARKETING_DOMAIN:-${ROOT_DOMAIN:-vatranscribe.ru}}"
APP_DOMAIN="${APP_DOMAIN:-app.vatranscribe.ru}"
API_DOMAIN="${API_DOMAIN:-api.vatranscribe.ru}"
API_HEALTH_PATH="${API_HEALTH_PATH:-/api/v1/health/live}"
CDN_STATIC_TEST_URLS="${CDN_STATIC_TEST_URLS:-}"

fetch_headers() {
  local url="$1"
  curl -fsSI --max-time 20 "${url}" | tr -d '\r'
}

assert_cache_policy_contains() {
  local url="$1"
  local expected_regex="$2"
  local label="$3"
  local headers cache_control
  headers="$(fetch_headers "${url}" || true)"
  [[ -n "${headers}" ]] || fail "HEAD request failed for ${label}: ${url}"
  echo "HEADERS_BEGIN=${label}"
  echo "${headers}" | sed -n '1,60p'
  echo "HEADERS_END=${label}"
  cache_control="$(echo "${headers}" | grep -i '^cache-control:' || true)"
  [[ -n "${cache_control}" ]] || fail "Cache-Control header is missing for ${label}: ${url}"
  echo "CACHE_CONTROL_${label}=${cache_control}"
  echo "${cache_control}" | grep -Eiq "${expected_regex}" || fail "Cache-Control for ${label} does not match ${expected_regex}: ${cache_control}"
  ok "${label} cache policy validated"
}

info "CDN provider: ${CDN_PROVIDER}"
echo "CDN_API_ENABLED=${CDN_API_ENABLED}"
echo "CDN_MARKETING_STATIC_ENABLED=${CDN_MARKETING_STATIC_ENABLED}"
echo "CDN_APP_STATIC_ENABLED=${CDN_APP_STATIC_ENABLED}"
echo "CDN_HTML_CACHE_POLICY=${CDN_HTML_CACHE_POLICY}"
echo "CDN_ASSET_CACHE_SECONDS=${CDN_ASSET_CACHE_SECONDS}"

assert_cache_policy_contains "https://${MARKETING_DOMAIN}/" "no-cache|no-store|max-age=0|must-revalidate" "marketing_html"
assert_cache_policy_contains "https://${APP_DOMAIN}/" "no-cache|no-store|max-age=0|must-revalidate" "app_html"
assert_cache_policy_contains "https://${API_DOMAIN}${API_HEALTH_PATH}" "no-store|no-cache|max-age=0|must-revalidate" "api_health"

if [[ "${CDN_API_ENABLED}" == "true" ]]; then
  fail "CDN_API_ENABLED must remain false for production API endpoints unless a dedicated API cache-bypass policy exists"
fi

if [[ -n "${CDN_STATIC_TEST_URLS}" ]]; then
  IFS=',' read -r -a urls <<< "${CDN_STATIC_TEST_URLS}"
  for raw_url in "${urls[@]}"; do
    url="$(echo "${raw_url}" | xargs)"
    [[ -n "${url}" ]] || continue
    assert_cache_policy_contains "${url}" "public|max-age=${CDN_ASSET_CACHE_SECONDS}|immutable" "static_asset"
  done
else
  info "CDN_STATIC_TEST_URLS is not set; static asset HIT/MISS check is skipped. Set it to one or more hashed asset URLs for production evidence."
fi

ok "CDN/cache live validation passed"
