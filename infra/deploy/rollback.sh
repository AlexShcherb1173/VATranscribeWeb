#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

PROJECT_ROOT="${PROJECT_ROOT:-/opt/vatranscribe/app}"
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
CERTBOT_ROOT="${CERTBOT_ROOT:-/opt/vatranscribe/certbot}"
ROLLBACK_SOURCE="${1:-}"
LOCK_FILE="${LOCK_FILE:-/tmp/vatranscribe-release-activation.lock}"

[[ -n "${ROLLBACK_SOURCE}" ]] || { echo "Usage: $0 <app.prev.directory>" >&2; exit 64; }
[[ -d "${PROJECT_ROOT}" ]] || { echo "Current project root not found." >&2; exit 66; }
[[ -d "${ROLLBACK_SOURCE}" ]] || { echo "Rollback directory not found." >&2; exit 66; }
[[ -f "${RUNTIME_ENV_FILE}" ]] || { echo "Runtime env file not found." >&2; exit 66; }

PROJECT_PARENT="$(dirname "${PROJECT_ROOT}")"
ROLLBACK_SOURCE="$(realpath "${ROLLBACK_SOURCE}")"

[[ "$(dirname "${ROLLBACK_SOURCE}")" == "${PROJECT_PARENT}" ]] || {
  echo "Rollback directory must be inside ${PROJECT_PARENT}." >&2
  exit 65
}

case "$(basename "${ROLLBACK_SOURCE}")" in
  app.prev.*) ;;
  *)
    echo "Rollback directory must match app.prev.*." >&2
    exit 65
    ;;
esac

BROKEN_ROOT="${PROJECT_PARENT}/app.broken.rollback.$(date -u +%Y%m%dT%H%M%SZ)-$$"
ROTATED="false"

compose_from_root() {
  local root="$1"
  shift
  (
    cd "${root}"
    # shellcheck disable=SC2086
    docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} "$@"
  )
}

restore_current_release() {
  local status=$?
  trap - ERR

  if [[ "${ROTATED}" == "true" ]]; then
    set +e

    echo "Rollback activation failed; restoring current release." >&2

    if [[ -d "${PROJECT_ROOT}" ]]; then
      mv "${PROJECT_ROOT}" "${ROLLBACK_SOURCE}"
    fi

    if [[ -d "${BROKEN_ROOT}" ]]; then
      mv "${BROKEN_ROOT}" "${PROJECT_ROOT}"
    fi

    if [[ -d "${PROJECT_ROOT}" ]]; then
      ln -sfn "${RUNTIME_ENV_FILE}" "${PROJECT_ROOT}/.env"
      rm -rf "${PROJECT_ROOT}/infra/certbot"
      ln -sfn "${CERTBOT_ROOT}" "${PROJECT_ROOT}/infra/certbot"
      compose_from_root "${PROJECT_ROOT}" build
      compose_from_root "${PROJECT_ROOT}" up -d db redis
      compose_from_root "${PROJECT_ROOT}" up -d --remove-orphans --force-recreate --no-deps api worker web
    fi
  fi

  exit "${status}"
}

trap restore_current_release ERR

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo "Another deployment or rollback is already running." >&2
  exit 75
fi

PROJECT_ROOT="${PROJECT_ROOT}" \
PROJECT_NAME="${PROJECT_NAME}" \
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE}" \
COMPOSE_FILES="${COMPOSE_FILES}" \
  bash "${PROJECT_ROOT}/infra/backup/backup-postgres.sh"

mv "${PROJECT_ROOT}" "${BROKEN_ROOT}"
ROTATED="true"
mv "${ROLLBACK_SOURCE}" "${PROJECT_ROOT}"

ln -sfn "${RUNTIME_ENV_FILE}" "${PROJECT_ROOT}/.env"
rm -rf "${PROJECT_ROOT}/infra/certbot"
ln -sfn "${CERTBOT_ROOT}" "${PROJECT_ROOT}/infra/certbot"

cd "${PROJECT_ROOT}"
bash ./infra/deploy/validate-production-secrets.sh "${RUNTIME_ENV_FILE}"

# shellcheck disable=SC2086
docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} build

# shellcheck disable=SC2086
# Ensure stateful dependencies exist without forcing recreation.
# shellcheck disable=SC2086
docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} up -d db redis

# Recreate only services bound to files from the restored release.
# shellcheck disable=SC2086
docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} up -d --remove-orphans --force-recreate --no-deps api worker web

bash ./infra/deploy/smoke-test.sh

ROTATED="false"
trap - ERR

echo "Database downgrade is intentionally not automatic. Use reviewed restore/downgrade procedure if required."
