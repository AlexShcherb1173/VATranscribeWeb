#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT:-/srv/vatranscribe}"
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
ROLLBACK_REF="${1:-}"
[[ -n "${ROLLBACK_REF}" ]] || { echo "Usage: $0 <git-tag-or-commit>" >&2; exit 2; }
cd "${PROJECT_ROOT}"
./infra/backup/backup-postgres.sh
git fetch --all --tags --prune
git checkout "${ROLLBACK_REF}"
# shellcheck disable=SC2086
docker compose -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} build
# shellcheck disable=SC2086
docker compose -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} up -d --remove-orphans
./infra/deploy/smoke-test.sh
echo "Database downgrade is intentionally not automatic. Use reviewed restore/downgrade procedure if required."
