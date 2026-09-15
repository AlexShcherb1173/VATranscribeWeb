#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/../.."
  pwd
)"

OUTPUT_FILE="${1:?output JSON path is required}"

DOCKER_IMAGE="${
  PIP_AUDIT_DOCKER_IMAGE:-python:3.12-slim-bookworm
}"

PIP_AUDIT_VERSION="${
  PIP_AUDIT_VERSION:-2.10.1
}"

mkdir -p "$(dirname "$OUTPUT_FILE")"

OUTPUT_DIR="$(
  cd "$(dirname "$OUTPUT_FILE")"
  pwd
)"

OUTPUT_NAME="$(basename "$OUTPUT_FILE")"

rm -f "${OUTPUT_DIR}/${OUTPUT_NAME}"

if ! command -v docker >/dev/null 2>&1; then
  echo \
    "Docker is required for production-aligned pip-audit." \
    >&2
  exit 127
fi

docker run \
  --rm \
  --mount \
  "type=bind,source=${ROOT_DIR},target=/workspace,readonly" \
  --mount \
  "type=bind,source=${OUTPUT_DIR},target=/out" \
  "$DOCKER_IMAGE" \
  sh -lc "
set -eu

python - <<'PY'
import sys

print(
    'PIP_AUDIT_RUNTIME_PYTHON='
    + sys.version.split()[0]
)

if sys.version_info[:2] != (3, 12):
    raise SystemExit(
        'pip-audit runtime must use Python 3.12'
    )
PY

python -m pip install \
  --disable-pip-version-check \
  --no-cache-dir \
  'pip-audit==${PIP_AUDIT_VERSION}'

python -m pip_audit --version

cd /workspace

python -m pip_audit . \
  --strict \
  --progress-spinner off \
  --timeout 60 \
  --format json \
  --output '/out/${OUTPUT_NAME}'
"

test -f "${OUTPUT_DIR}/${OUTPUT_NAME}"
