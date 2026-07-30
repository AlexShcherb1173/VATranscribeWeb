#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

PROJECT_ROOT="${PROJECT_ROOT:-/srv/vatranscribe}"
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"

NGINX_RUNTIME_UID="${NGINX_RUNTIME_UID:-101}"
NGINX_RUNTIME_GID="${NGINX_RUNTIME_GID:-101}"

fail() {
  echo "[ERROR] $*" >&2
  exit 1
}

info() {
  echo "[INFO] $*" >&2
}

cd "${PROJECT_ROOT}"

[[ -f "${RUNTIME_ENV_FILE}" ]] ||
  fail "Runtime env file not found: ${RUNTIME_ENV_FILE}"

# shellcheck disable=SC1090
set -a
source "${RUNTIME_ENV_FILE}"
set +a

CERTBOT_PRIMARY_DOMAIN="${CERTBOT_PRIMARY_DOMAIN:-${ROOT_DOMAIN:-vatranscribe.ru}}"

if [[ ! "${CERTBOT_PRIMARY_DOMAIN}" =~ ^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$ ]]; then
  fail "Invalid CERTBOT_PRIMARY_DOMAIN: ${CERTBOT_PRIMARY_DOMAIN}"
fi

if [[ "${CERTBOT_PRIMARY_DOMAIN}" == *..* ]]; then
  fail "Invalid CERTBOT_PRIMARY_DOMAIN: ${CERTBOT_PRIMARY_DOMAIN}"
fi

if [[ ! "${NGINX_RUNTIME_UID}" =~ ^[0-9]+$ ]]; then
  fail "Invalid NGINX_RUNTIME_UID: ${NGINX_RUNTIME_UID}"
fi

if [[ ! "${NGINX_RUNTIME_GID}" =~ ^[0-9]+$ ]]; then
  fail "Invalid NGINX_RUNTIME_GID: ${NGINX_RUNTIME_GID}"
fi

compose() {
  # COMPOSE_FILES intentionally contains separate Docker Compose arguments.
  # shellcheck disable=SC2086
  docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} "$@"
}

read -r -d '' sync_command <<'SYNC_COMMAND' || true
set -eu
umask 077

domain="$1"
runtime_uid="$2"
runtime_gid="$3"

source_dir="/etc/letsencrypt/live/${domain}"
runtime_root="/etc/nginx-certs"
releases_root="${runtime_root}/releases"
live_root="${runtime_root}/live"

release_name="$(date -u +%Y%m%dT%H%M%SZ)-$$"
release_dir="${releases_root}/${release_name}"

fullchain_source="${source_dir}/fullchain.pem"
privkey_source="${source_dir}/privkey.pem"

test -s "${fullchain_source}"
test -s "${privkey_source}"

mkdir -p "${runtime_root}"
mkdir -p "${releases_root}"
mkdir -p "${live_root}"
mkdir -p "${release_dir}"

chown "${runtime_uid}:${runtime_gid}" "${runtime_root}"
chown "${runtime_uid}:${runtime_gid}" "${releases_root}"
chown "${runtime_uid}:${runtime_gid}" "${live_root}"

chmod 0550 "${runtime_root}"
chmod 0550 "${releases_root}"
chmod 0550 "${live_root}"

cp -L "${fullchain_source}" "${release_dir}/fullchain.pem"
cp -L "${privkey_source}" "${release_dir}/privkey.pem"

chown "${runtime_uid}:${runtime_gid}" "${release_dir}"
chown "${runtime_uid}:${runtime_gid}" "${release_dir}/fullchain.pem"
chown "${runtime_uid}:${runtime_gid}" "${release_dir}/privkey.pem"

chmod 0550 "${release_dir}"
chmod 0444 "${release_dir}/fullchain.pem"
chmod 0400 "${release_dir}/privkey.pem"

python - \
  "${runtime_root}" \
  "${domain}" \
  "${release_name}" \
  "${runtime_uid}" \
  "${runtime_gid}" <<'PY'
from __future__ import annotations

import os
import pathlib
import sys


runtime_root = pathlib.Path(sys.argv[1])
domain = sys.argv[2]
release_name = sys.argv[3]
runtime_uid = int(sys.argv[4])
runtime_gid = int(sys.argv[5])

live_root = runtime_root / "live"
current_link = live_root / domain
temporary_link = live_root / f".{domain}.tmp.{os.getpid()}"

target = pathlib.Path("..") / "releases" / release_name

if current_link.exists() and not current_link.is_symlink():
    raise RuntimeError(
        f"Runtime certificate target is not a symlink: {current_link}"
    )

try:
    temporary_link.unlink()
except FileNotFoundError:
    pass

temporary_link.symlink_to(
    target,
    target_is_directory=True,
)

os.replace(
    temporary_link,
    current_link,
)

fullchain_path = current_link / "fullchain.pem"
privkey_path = current_link / "privkey.pem"

child_pid = os.fork()

if child_pid == 0:
    try:
        os.setgroups([])
        os.setgid(runtime_gid)
        os.setuid(runtime_uid)

        with fullchain_path.open("rb") as certificate_file:
            if not certificate_file.read(1):
                raise RuntimeError("Runtime fullchain is empty")

        with privkey_path.open("rb") as private_key_file:
            if not private_key_file.read(1):
                raise RuntimeError("Runtime private key is empty")
    except BaseException:
        os._exit(1)

    os._exit(0)

_, wait_status = os.waitpid(child_pid, 0)

if not os.WIFEXITED(wait_status):
    raise RuntimeError(
        "Runtime certificate readability check terminated unexpectedly"
    )

if os.WEXITSTATUS(wait_status) != 0:
    raise RuntimeError(
        "Nginx runtime UID/GID cannot read synchronized certificate files"
    )
PY

test -r "${live_root}/${domain}/fullchain.pem"
test -r "${live_root}/${domain}/privkey.pem"

stat -c '%u:%g %a %s %n' \
  "${live_root}/${domain}/fullchain.pem" \
  "${live_root}/${domain}/privkey.pem"

echo "NGINX_CERTIFICATE_SYNC_OK"
SYNC_COMMAND

info "Synchronizing certificate for ${CERTBOT_PRIMARY_DOMAIN}"

compose run \
  --rm \
  --entrypoint /bin/sh \
  certbot \
  -ceu \
  "${sync_command}" \
  -- \
  "${CERTBOT_PRIMARY_DOMAIN}" \
  "${NGINX_RUNTIME_UID}" \
  "${NGINX_RUNTIME_GID}"

info "Nginx runtime certificate volume synchronized"
