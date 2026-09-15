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
EXPECTED_IP="${PRODUCTION_HOST_PUBLIC_IP:-}"
CHECK_DNS_EXPECTED_IP="${CHECK_DNS_EXPECTED_IP:-false}"
DNS_REQUIRE_CAA="${DNS_REQUIRE_CAA:-false}"
DNS_PROVIDER="${DNS_PROVIDER:-manual DNS}"

have_dig=false
if command -v dig >/dev/null 2>&1; then
  have_dig=true
fi

resolve_a() {
  local domain="$1"
  if [[ "${have_dig}" == "true" ]]; then
    dig +short A "${domain}" | sed '/^$/d' || true
  elif command -v getent >/dev/null 2>&1; then
    getent ahostsv4 "${domain}" | awk '{print $1}' | sort -u || true
  else
    fail "dig or getent is required for DNS checks"
  fi
}

resolve_aaaa() {
  local domain="$1"
  if [[ "${have_dig}" == "true" ]]; then
    dig +short AAAA "${domain}" | sed '/^$/d' || true
  else
    true
  fi
}

resolve_cname() {
  local domain="$1"
  if [[ "${have_dig}" == "true" ]]; then
    dig +short CNAME "${domain}" | sed '/^$/d' || true
  else
    true
  fi
}

resolve_caa() {
  local domain="$1"
  if [[ "${have_dig}" == "true" ]]; then
    dig +short CAA "${domain}" | sed '/^$/d' || true
  else
    true
  fi
}

info "DNS provider: ${DNS_PROVIDER}"
info "Runtime env source: ${RUNTIME_ENV_FILE}"

IFS=',' read -r -a domains <<< "${DOMAINS_CSV}"
[[ "${#domains[@]}" -gt 0 ]] || fail "No domains configured"

for raw_domain in "${domains[@]}"; do
  domain="$(echo "${raw_domain}" | xargs)"
  [[ -n "${domain}" ]] || continue

  info "Checking DNS for ${domain}"
  mapfile -t a_records < <(resolve_a "${domain}")
  mapfile -t aaaa_records < <(resolve_aaaa "${domain}")
  cname_records="$(resolve_cname "${domain}" | paste -sd ',' - || true)"
  caa_records="$(resolve_caa "${domain}" | paste -sd ';' - || true)"

  if [[ "${#a_records[@]}" -eq 0 && "${#aaaa_records[@]}" -eq 0 && -z "${cname_records}" ]]; then
    fail "${domain} has no A, AAAA, or CNAME DNS result"
  fi

  echo "DNS_DOMAIN=${domain}"
  echo "DNS_A_RECORDS=$(IFS=','; echo "${a_records[*]:-}")"
  echo "DNS_AAAA_RECORDS=$(IFS=','; echo "${aaaa_records[*]:-}")"
  echo "DNS_CNAME_RECORDS=${cname_records:-none}"
  echo "DNS_CAA_RECORDS=${caa_records:-none}"

  if [[ "${CHECK_DNS_EXPECTED_IP}" == "true" ]]; then
    [[ -n "${EXPECTED_IP}" ]] || fail "PRODUCTION_HOST_PUBLIC_IP is required when CHECK_DNS_EXPECTED_IP=true"
    found=false
    for ip in "${a_records[@]}" "${aaaa_records[@]}"; do
      if [[ "${ip}" == "${EXPECTED_IP}" ]]; then
        found=true
        break
      fi
    done
    [[ "${found}" == "true" ]] || fail "${domain} does not resolve to expected PRODUCTION_HOST_PUBLIC_IP"
    ok "${domain} resolves to expected production IP"
  fi

  if [[ "${DNS_REQUIRE_CAA}" == "true" ]]; then
    [[ -n "${caa_records}" ]] || fail "${domain} has no CAA record and DNS_REQUIRE_CAA=true"
    ok "${domain} has CAA record"
  fi
done

ok "DNS live validation passed"
