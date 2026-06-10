#!/usr/bin/env bash
set -euo pipefail

fail() { echo "[ERROR] $*" >&2; exit 1; }
info() { echo "[INFO] $*" >&2; }

PROJECT_ROOT="${PROJECT_ROOT:-/srv/vatranscribe}"
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"

cd "${PROJECT_ROOT}"
[[ -f "${RUNTIME_ENV_FILE}" ]] || fail "Runtime env file not found: ${RUNTIME_ENV_FILE}"
# shellcheck disable=SC1090
set -a; source "${RUNTIME_ENV_FILE}"; set +a

CERTBOT_EMAIL="${CERTBOT_EMAIL:?CERTBOT_EMAIL is required}"
CERTBOT_DOMAINS="${CERTBOT_DOMAINS:?CERTBOT_DOMAINS is required}"
CERTBOT_PRIMARY_DOMAIN="${CERTBOT_PRIMARY_DOMAIN:-${ROOT_DOMAIN:-vatranscribe.ru}}"
CERTBOT_STAGING="${CERTBOT_STAGING:-false}"
CERTBOT_RSA_KEY_SIZE="${CERTBOT_RSA_KEY_SIZE:-4096}"

compose() {
  # shellcheck disable=SC2086
  docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} "$@"
}

mkdir -p infra/certbot/conf/live/"${CERTBOT_PRIMARY_DOMAIN}" infra/certbot/www

if [[ ! -f "infra/certbot/conf/live/${CERTBOT_PRIMARY_DOMAIN}/fullchain.pem" || ! -f "infra/certbot/conf/live/${CERTBOT_PRIMARY_DOMAIN}/privkey.pem" ]]; then
  info "Creating temporary self-signed certificate for nginx bootstrap"
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "infra/certbot/conf/live/${CERTBOT_PRIMARY_DOMAIN}/privkey.pem" \
    -out "infra/certbot/conf/live/${CERTBOT_PRIMARY_DOMAIN}/fullchain.pem" \
    -subj "/CN=${CERTBOT_PRIMARY_DOMAIN}"
fi

info "Starting nginx/web for HTTP-01 challenge"
compose up -d web

args=(certonly --webroot -w /var/www/certbot --agree-tos --non-interactive --email "${CERTBOT_EMAIL}" --rsa-key-size "${CERTBOT_RSA_KEY_SIZE}" --keep-until-expiring)
if [[ "${CERTBOT_STAGING}" == "true" ]]; then
  args+=(--staging)
fi

IFS=',' read -r -a domains <<< "${CERTBOT_DOMAINS}"
for raw_domain in "${domains[@]}"; do
  domain="$(echo "${raw_domain}" | xargs)"
  [[ -n "${domain}" ]] && args+=(-d "${domain}")
done

info "Requesting Let's Encrypt certificate for: ${CERTBOT_DOMAINS}"
compose run --rm certbot "${args[@]}"

info "Reloading nginx"
compose exec -T web nginx -s reload
info "Certificate issue completed"
