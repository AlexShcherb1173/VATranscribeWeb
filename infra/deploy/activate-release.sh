#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

RELEASE_ARCHIVE="${1:-${RELEASE_ARCHIVE:-}}"
RELEASE_CHECKSUM="${2:-${RELEASE_CHECKSUM:-}}"
PROJECT_ROOT="${PROJECT_ROOT:-/opt/vatranscribe/app}"
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
CERTBOT_ROOT="${CERTBOT_ROOT:-/opt/vatranscribe/certbot}"
SMOKE_BASE_URL="${SMOKE_BASE_URL:-https://api.vatranscribe.ru}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
LOCK_FILE="${LOCK_FILE:-/tmp/vatranscribe-release-activation.lock}"
RELEASE_RETENTION_COUNT="${RELEASE_RETENTION_COUNT:-3}"

[[ -n "${RELEASE_ARCHIVE}" ]] || { echo "Release archive is required." >&2; exit 64; }
[[ -n "${RELEASE_CHECKSUM}" ]] || { echo "Release checksum is required." >&2; exit 64; }
[[ -f "${RELEASE_ARCHIVE}" ]] || { echo "Release archive not found." >&2; exit 66; }
[[ -f "${RELEASE_CHECKSUM}" ]] || { echo "Release checksum not found." >&2; exit 66; }
[[ -d "${PROJECT_ROOT}" ]] || { echo "Project root not found." >&2; exit 66; }
[[ -f "${RUNTIME_ENV_FILE}" ]] || { echo "Runtime env file not found." >&2; exit 66; }
[[ -d "${CERTBOT_ROOT}" ]] || { echo "Certbot runtime root not found." >&2; exit 66; }

PROJECT_ROOT="$(realpath -m "${PROJECT_ROOT}")"
RUNTIME_ENV_FILE="$(realpath -m "${RUNTIME_ENV_FILE}")"
CERTBOT_ROOT="$(realpath -m "${CERTBOT_ROOT}")"
PROJECT_PARENT="$(dirname "${PROJECT_ROOT}")"

[[ "$(basename "${PROJECT_ROOT}")" == "app" ]] || {
  echo "Project root must end with /app." >&2
  exit 65
}

[[ "$(dirname "${CERTBOT_ROOT}")" == "${PROJECT_PARENT}" ]] || {
  echo "Certbot root must be a sibling of the project root." >&2
  exit 65
}

[[ "$(basename "${CERTBOT_ROOT}")" == "certbot" ]] || {
  echo "Unexpected Certbot root name." >&2
  exit 65
}

[[ -d "${PROJECT_PARENT}" && -w "${PROJECT_PARENT}" ]] || {
  echo "Project parent is not writable." >&2
  exit 73
}

RELEASE_ID="${RELEASE_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}"

[[ "${RELEASE_ID}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$ ]] || {
  echo "Release ID contains unsupported characters." >&2
  exit 65
}

[[ "${RELEASE_RETENTION_COUNT}" =~ ^[0-9]+$ ]] || {
  echo "RELEASE_RETENTION_COUNT must be an integer." >&2
  exit 65
}

if (( RELEASE_RETENTION_COUNT < 1 || RELEASE_RETENTION_COUNT > 20 )); then
  echo "RELEASE_RETENTION_COUNT must be between 1 and 20." >&2
  exit 65
fi

STAGING_ROOT="${PROJECT_PARENT}/app.next.${RELEASE_ID}"
PREVIOUS_ROOT="${PROJECT_PARENT}/app.prev.${RELEASE_ID}"
BROKEN_ROOT="${PROJECT_PARENT}/app.broken.${RELEASE_ID}"
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

prune_release_directories() {
  local pattern="$1"
  local keep_count="$2"
  local entry directory basename_value
  local seen=0

  while IFS= read -r -d '' entry; do
    directory="${entry#* }"
    seen=$((seen + 1))

    if (( seen <= keep_count )); then
      continue
    fi

    [[ "$(dirname "${directory}")" == "${PROJECT_PARENT}" ]] || continue
    basename_value="$(basename "${directory}")"

    case "${basename_value}" in
      app.prev.*|app.broken.*)
        rm -rf -- "${directory}"
        ;;
    esac
  done < <(
    find "${PROJECT_PARENT}" \
      -mindepth 1 \
      -maxdepth 1 \
      -type d \
      -name "${pattern}" \
      -printf '%T@ %p\0' |
      sort -z -nr
  )
}

restore_previous_release() {
  if [[ "${ROTATED}" != "true" ]]; then
    return 0
  fi

  set +e
  echo "Release activation failed; restoring previous release." >&2

  if [[ -d "${PROJECT_ROOT}" ]]; then
    mv "${PROJECT_ROOT}" "${BROKEN_ROOT}"
  fi

  if [[ -d "${PREVIOUS_ROOT}" ]]; then
    mv "${PREVIOUS_ROOT}" "${PROJECT_ROOT}"
  fi

  if [[ -d "${PROJECT_ROOT}" ]]; then
    ln -sfn "${RUNTIME_ENV_FILE}" "${PROJECT_ROOT}/.env"
    rm -rf "${PROJECT_ROOT}/infra/certbot"
    ln -sfn "${CERTBOT_ROOT}" "${PROJECT_ROOT}/infra/certbot"
    compose_from_root "${PROJECT_ROOT}" build
    compose_from_root "${PROJECT_ROOT}" up -d db redis
    compose_from_root "${PROJECT_ROOT}" up -d --remove-orphans --force-recreate --no-deps api worker web
  fi

  ROTATED="false"
  set -e
}

cleanup() {
  local status=$?
  trap - EXIT

  if [[ "${status}" -ne 0 ]]; then
    restore_previous_release || true
  fi

  rm -rf "${STAGING_ROOT}"
  rm -f "${RELEASE_ARCHIVE}" "${RELEASE_CHECKSUM}"

  case "$0" in
    /tmp/vatranscribe-*.activate-release.sh)
      rm -f "$0"
      ;;
  esac
  exit "${status}"
}

trap cleanup EXIT

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo "Another release activation is already running." >&2
  exit 75
fi

checksum_directory="$(dirname "${RELEASE_CHECKSUM}")"
archive_directory="$(dirname "${RELEASE_ARCHIVE}")"

[[ "${checksum_directory}" == "${archive_directory}" ]] || {
  echo "Archive and checksum must be in the same directory." >&2
  exit 65
}

checksum_line_count="$(awk 'NF { count++ } END { print count + 0 }' "${RELEASE_CHECKSUM}")"

[[ "${checksum_line_count}" == "1" ]] || {
  echo "Checksum file must contain exactly one non-empty line." >&2
  exit 65
}

expected_sha="$(awk 'NF { print $1; exit }' "${RELEASE_CHECKSUM}")"

[[ "${expected_sha}" =~ ^[0-9a-fA-F]{64}$ ]] || {
  echo "Checksum file contains an invalid SHA-256 value." >&2
  exit 65
}

actual_sha="$(sha256sum "${RELEASE_ARCHIVE}" | awk '{ print $1 }')"

[[ "${actual_sha,,}" == "${expected_sha,,}" ]] || {
  echo "Release archive SHA-256 mismatch." >&2
  exit 65
}

while IFS= read -r archive_path; do
  [[ -n "${archive_path}" ]] || continue

  case "${archive_path}" in
    /*|..|../*|*/..|*/../*)
      echo "Archive contains unsafe path: ${archive_path}" >&2
      exit 65
      ;;
  esac
done < <(tar -tzf "${RELEASE_ARCHIVE}")

mkdir -p "${STAGING_ROOT}"
chmod 775 "${STAGING_ROOT}"

tar \
  --extract \
  --gzip \
  --file "${RELEASE_ARCHIVE}" \
  --directory "${STAGING_ROOT}" \
  --no-same-owner \
  --no-same-permissions \
  --delay-directory-restore

if find "${STAGING_ROOT}" -xdev -type l -print -quit | grep -q .; then
  echo "Release archive contains a symbolic link." >&2
  exit 65
fi

if find "${STAGING_ROOT}" -xdev \
  ! -type f \
  ! -type d \
  -print -quit | grep -q .; then
  echo "Release archive contains an unsupported filesystem entry." >&2
  exit 65
fi

for required in \
  docker-compose.yml \
  infra/compose/docker-compose.prod.yml \
  infra/deploy/deploy.sh \
  infra/deploy/validate-production-secrets.sh \
  infra/backup/backup-postgres.sh; do
  [[ -f "${STAGING_ROOT}/${required}" ]] || {
    echo "Required release file is missing: ${required}" >&2
    exit 66
  }
done

bash "${STAGING_ROOT}/infra/deploy/validate-production-secrets.sh" "${RUNTIME_ENV_FILE}"
ln -sfn "${RUNTIME_ENV_FILE}" "${STAGING_ROOT}/.env"

rm -rf "${STAGING_ROOT}/infra/certbot"
ln -sfn "${CERTBOT_ROOT}" "${STAGING_ROOT}/infra/certbot"

if [[ -d "${PROJECT_ROOT}/infra/deploy/.p3-02-backups" ]]; then
  mkdir -p "${STAGING_ROOT}/infra/deploy"
  cp -a \
    "${PROJECT_ROOT}/infra/deploy/.p3-02-backups" \
    "${STAGING_ROOT}/infra/deploy/"
fi

(
  cd "${PROJECT_ROOT}"
  PROJECT_ROOT="${PROJECT_ROOT}" \
  PROJECT_NAME="${PROJECT_NAME}" \
  RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE}" \
  COMPOSE_FILES="${COMPOSE_FILES}" \
    bash "${STAGING_ROOT}/infra/backup/backup-postgres.sh"
)

[[ ! -e "${PREVIOUS_ROOT}" ]] || { echo "Previous release target already exists." >&2; exit 73; }

mv "${PROJECT_ROOT}" "${PREVIOUS_ROOT}"
ROTATED="true"
mv "${STAGING_ROOT}" "${PROJECT_ROOT}"

PROJECT_ROOT="${PROJECT_ROOT}" \
PROJECT_NAME="${PROJECT_NAME}" \
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE}" \
SMOKE_BASE_URL="${SMOKE_BASE_URL}" \
COMPOSE_FILES="${COMPOSE_FILES}" \
BACKUP_BEFORE_DEPLOY="false" \
  bash "${PROJECT_ROOT}/infra/deploy/deploy.sh"

prune_release_directories "app.prev.*" "${RELEASE_RETENTION_COUNT}"
prune_release_directories "app.broken.*" "${RELEASE_RETENTION_COUNT}"

ROTATED="false"
echo "Release activation completed: ${PROJECT_ROOT}"
