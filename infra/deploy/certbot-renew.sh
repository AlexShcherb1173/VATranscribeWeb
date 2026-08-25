#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/opt/vatranscribe/app}"
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"

[[ -f "${RUNTIME_ENV_FILE}" ]] || {
  echo "[ERROR] Runtime env file not found: ${RUNTIME_ENV_FILE}" >&2
  exit 1
}

# Runtime env is rendered with shell-safe values by render-runtime-env.sh.
# shellcheck disable=SC1090
set -a
source "${RUNTIME_ENV_FILE}"
set +a

cd "${PROJECT_ROOT}"

compose() {
  # shellcheck disable=SC2086
  docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} "$@"
}

compose run -T --rm certbot renew --webroot -w /var/www/certbot

bash infra/deploy/sync-nginx-certificates.sh

if [[ "${CERTBOT_RENEW_DEPLOY_HOOK_RELOAD:-true}" == "true" ]]; then
  compose exec -T web nginx -s reload
fi
