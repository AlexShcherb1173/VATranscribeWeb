#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/opt/vatranscribe/app}"
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
cd "${PROJECT_ROOT}"

compose() {
  # shellcheck disable=SC2086
  docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} "$@"
}

compose run -T --rm certbot renew --dry-run --webroot -w /var/www/certbot
if [[ "${CERTBOT_RENEW_DEPLOY_HOOK_RELOAD:-true}" == "true" ]]; then
  true # dry-run does not require nginx reload
fi
