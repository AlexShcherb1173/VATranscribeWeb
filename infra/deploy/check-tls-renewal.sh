#!/usr/bin/env bash
set -euo pipefail

fail() { echo "[ERROR] $*" >&2; exit 1; }
info() { echo "[INFO] $*" >&2; }

RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
if [[ -f "${RUNTIME_ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  set -a; source "${RUNTIME_ENV_FILE}"; set +a
fi

DOMAINS_CSV="${CERTBOT_DOMAINS:-${ROOT_DOMAIN:-vatranscribe.ru},${APP_DOMAIN:-app.vatranscribe.ru},${API_DOMAIN:-api.vatranscribe.ru},${ADMIN_DOMAIN:-admin.vatranscribe.ru}}"
WARN_DAYS="${TLS_EXPIRY_WARN_DAYS:-21}"
WARN_SECONDS=$((WARN_DAYS * 86400))

IFS=',' read -r -a domains <<< "${DOMAINS_CSV}"
for raw_domain in "${domains[@]}"; do
  domain="$(echo "${raw_domain}" | xargs)"
  [[ -n "${domain}" ]] || continue
  info "Checking TLS certificate for ${domain}"
  if ! echo | openssl s_client -servername "${domain}" -connect "${domain}:443" 2>/dev/null | openssl x509 -checkend "${WARN_SECONDS}" -noout; then
    fail "TLS certificate for ${domain} expires within ${WARN_DAYS} days or is not reachable"
  fi
  echo | openssl s_client -servername "${domain}" -connect "${domain}:443" 2>/dev/null | openssl x509 -noout -subject -issuer -dates
done

info "TLS renewal checks passed"
