#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/opt/vatranscribe/app}"
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"

cd "${PROJECT_ROOT}"

bash ./infra/deploy/validate-production-secrets.sh "${RUNTIME_ENV_FILE}"
ln -sfn "${RUNTIME_ENV_FILE}" "${PROJECT_ROOT}/.env"

if [[ "${CHECK_DOMAIN_READINESS:-false}" == "true" ]]; then
  bash ./infra/deploy/check-domain-readiness.sh
fi

if [[ "${BACKUP_BEFORE_DEPLOY}" == "true" ]]; then
  PROJECT_ROOT="${PROJECT_ROOT}" \
  PROJECT_NAME="${PROJECT_NAME}" \
  RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE}" \
  COMPOSE_FILES="${COMPOSE_FILES}" \
    bash ./infra/backup/backup-postgres.sh
fi

# shellcheck disable=SC2086
docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} build

if [[ "${RUN_MIGRATIONS}" == "true" ]]; then
  # shellcheck disable=SC2086
  docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} run --rm api python -m alembic upgrade head
fi

# shellcheck disable=SC2086
# Ensure stateful dependencies exist without forcing recreation.
# shellcheck disable=SC2086
docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} up -d db redis

# Recreate only services that consume the activated application release.
# shellcheck disable=SC2086
docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} up -d --remove-orphans --force-recreate --no-deps api worker web

bash ./infra/deploy/smoke-test.sh
bash ./infra/deploy/monitoring-smoke.sh
