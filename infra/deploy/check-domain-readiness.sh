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
EXPECTED_IP="${PRODUCTION_HOST_PUBLIC_IP:-}"
CHECK_DNS_EXPECTED_IP="${CHECK_DNS_EXPECTED_IP:-true}"

IFS=',' read -r -a domains <<< "${DOMAINS_CSV}"
[[ "${#domains[@]}" -gt 0 ]] || fail "No domains configured"

for raw_domain in "${domains[@]}"; do
  domain="$(echo "${raw_domain}" | xargs)"
  [[ -n "${domain}" ]] || continue
  info "Checking DNS for ${domain}"
  resolved=""
  if command -v dig >/dev/null 2>&1; then
    resolved="$(dig +short A "${domain}" | tail -n 1 || true)"
  elif command -v getent >/dev/null 2>&1; then
    resolved="$(getent ahostsv4 "${domain}" | awk '{print $1; exit}' || true)"
  else
    fail "dig or getent is required for DNS readiness checks"
  fi
  [[ -n "${resolved}" ]] || fail "${domain} does not resolve to an A record"
  info "${domain} -> ${resolved}"
  if [[ "${CHECK_DNS_EXPECTED_IP}" == "true" ]]; then
    [[ -n "${EXPECTED_IP}" ]] || fail "PRODUCTION_HOST_PUBLIC_IP is required when CHECK_DNS_EXPECTED_IP=true"
    [[ "${resolved}" == "${EXPECTED_IP}" ]] || fail "${domain} resolves to ${resolved}, expected ${EXPECTED_IP}"
  fi
done

info "Domain readiness checks passed"
