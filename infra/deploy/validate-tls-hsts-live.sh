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

DOMAINS_CSV="${CERTBOT_DOMAINS:-${ROOT_DOMAIN:-vatranscribe.ru},${APP_DOMAIN:-app.vatranscribe.ru},${API_DOMAIN:-api.vatranscribe.ru},${ADMIN_DOMAIN:-admin.vatranscribe.ru}}"
WARN_DAYS="${TLS_EXPIRY_WARN_DAYS:-21}"
WARN_SECONDS=$((WARN_DAYS * 86400))
HSTS_REQUIRED="${HSTS_REQUIRED:-true}"
HTTP_TO_HTTPS_REDIRECT_REQUIRED="${HTTP_TO_HTTPS_REDIRECT_REQUIRED:-true}"
EXPECTED_HSTS_MAX_AGE="${NGINX_HSTS_MAX_AGE:-31536000}"

require_tool() {
  command -v "$1" >/dev/null 2>&1 || fail "$1 is required"
}

require_tool openssl
require_tool curl

IFS=',' read -r -a domains <<< "${DOMAINS_CSV}"
[[ "${#domains[@]}" -gt 0 ]] || fail "No domains configured"

for raw_domain in "${domains[@]}"; do
  domain="$(echo "${raw_domain}" | xargs)"
  [[ -n "${domain}" ]] || continue

  info "Checking TLS certificate for ${domain}"
  cert_text="$(echo | openssl s_client -servername "${domain}" -connect "${domain}:443" 2>/dev/null | openssl x509 -noout -subject -issuer -dates)" || fail "TLS certificate is not reachable for ${domain}"
  echo "TLS_DOMAIN=${domain}"
  echo "${cert_text}"

  echo | openssl s_client -servername "${domain}" -connect "${domain}:443" 2>/dev/null | openssl x509 -checkend "${WARN_SECONDS}" -noout >/dev/null || fail "TLS certificate for ${domain} expires within ${WARN_DAYS} days"
  ok "TLS certificate expiry is outside warning window for ${domain}"

  info "Checking HTTPS headers for ${domain}"
  headers="$(curl -fsSI --max-time 15 "https://${domain}/" || true)"
  [[ -n "${headers}" ]] || fail "HTTPS HEAD request failed for ${domain}"
  echo "HTTPS_HEADERS_BEGIN=${domain}"
  echo "${headers}" | sed -n '1,40p'
  echo "HTTPS_HEADERS_END=${domain}"

  if [[ "${HSTS_REQUIRED}" == "true" ]]; then
    hsts="$(echo "${headers}" | tr -d '\r' | grep -i '^strict-transport-security:' || true)"
    [[ -n "${hsts}" ]] || fail "Strict-Transport-Security header is missing for ${domain}"
    echo "HSTS_HEADER=${hsts}"
    echo "${hsts}" | grep -Eq "max-age=([0-9]+)" || fail "HSTS max-age is missing for ${domain}"
    if [[ "${EXPECTED_HSTS_MAX_AGE}" != "0" ]]; then
      echo "${hsts}" | grep -q "max-age=${EXPECTED_HSTS_MAX_AGE}" || fail "HSTS max-age does not match expected ${EXPECTED_HSTS_MAX_AGE} for ${domain}"
    fi
    ok "HSTS header is present for ${domain}"
  fi

  if [[ "${HTTP_TO_HTTPS_REDIRECT_REQUIRED}" == "true" ]]; then
    redirect_headers="$(curl -sSI --max-time 15 "http://${domain}/" || true)"
    location="$(echo "${redirect_headers}" | tr -d '\r' | grep -i '^location:' || true)"
    [[ "${location}" == *"https://${domain}"* || "${location}" == *"https://"* ]] || fail "HTTP to HTTPS redirect is missing for ${domain}"
    echo "HTTP_REDIRECT_LOCATION=${location}"
    ok "HTTP redirects to HTTPS for ${domain}"
  fi
done

ok "TLS/HSTS live validation passed"
