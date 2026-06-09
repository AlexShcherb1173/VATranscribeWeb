#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-/srv/vatranscribe}"
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
GIT_REF="${GIT_REF:-main}"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"
cd "${PROJECT_ROOT}"
[[ "${BACKUP_BEFORE_DEPLOY}" == "true" ]] && ./infra/backup/backup-postgres.sh
git fetch --all --tags --prune
git checkout "${GIT_REF}"
git pull --ff-only || true
# shellcheck disable=SC2086
docker compose -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} build
if [[ "${RUN_MIGRATIONS}" == "true" ]]; then
  # shellcheck disable=SC2086
  docker compose -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} run --rm api python -m alembic upgrade head
fi
# shellcheck disable=SC2086
docker compose -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} up -d --remove-orphans
./infra/deploy/smoke-test.sh
