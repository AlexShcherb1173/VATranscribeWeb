#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/srv/vatranscribe}"
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
cd "${PROJECT_ROOT}"

compose() {
  # shellcheck disable=SC2086
  docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} "$@"
}

compose run --rm certbot renew --webroot -w /var/www/certbot
if [[ "${CERTBOT_RENEW_DEPLOY_HOOK_RELOAD:-true}" == "true" ]]; then
  compose exec -T web nginx -s reload
fi
