#!/usr/bin/env bash
set -euo pipefail

# P3-04 request_id propagation and log-search validation.
# Do not print secrets. This script validates HTTP propagation and prints a log-search marker.

RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
REQUEST_ID_HEADER="${REQUEST_ID_HEADER:-X-Request-ID}"
SMOKE_TIMEOUT_SECONDS="${SMOKE_TIMEOUT_SECONDS:-10}"
LOG_SEARCH_MODE="${LOG_SEARCH_MODE:-manual}"

if [[ -f "${RUNTIME_ENV_FILE}" ]]; then
  set -a
  # shellcheck source=/dev/null
  . "${RUNTIME_ENV_FILE}"
  set +a
fi

API_URL="${PUBLIC_API_ORIGIN:-https://api.vatranscribe.ru}"
REQUEST_ID="p3-04-$(python - <<'PY'
import uuid
print(uuid.uuid4().hex)
PY
)"
HEADERS_FILE="$(mktemp)"
BODY_FILE="$(mktemp)"
trap 'rm -f "${HEADERS_FILE}" "${BODY_FILE}"' EXIT

TARGET_URL="${API_URL%/}/api/v1/health/live"

echo "[INFO] Sending ${REQUEST_ID_HEADER}: ${REQUEST_ID} to ${TARGET_URL}"
status="$(curl --silent --show-error --max-time "${SMOKE_TIMEOUT_SECONDS}" \
  --header "${REQUEST_ID_HEADER}: ${REQUEST_ID}" \
  --dump-header "${HEADERS_FILE}" \
  --output "${BODY_FILE}" \
  --write-out '%{http_code}' \
  "${TARGET_URL}")"

if [[ "${status}" != "200" ]]; then
  echo "[FAIL] API live returned HTTP ${status}" >&2
  cat "${BODY_FILE}" >&2 || true
  exit 1
fi

if grep -qi "^${REQUEST_ID_HEADER}: ${REQUEST_ID}" "${HEADERS_FILE}"; then
  echo "[OK] Response contains ${REQUEST_ID_HEADER}: ${REQUEST_ID}"
else
  echo "[FAIL] Response does not contain expected ${REQUEST_ID_HEADER}" >&2
  cat "${HEADERS_FILE}" >&2 || true
  exit 1
fi

cat <<EOF
[INFO] Request ID log-search marker:
REQUEST_ID=${REQUEST_ID}

Manual Loki/Grafana query examples:
  {service="api"} |= "${REQUEST_ID}"
  {container="vatranscribe-api"} |= "${REQUEST_ID}"

Manual Docker fallback:
  docker compose --env-file ${RUNTIME_ENV_FILE} -f docker-compose.yml -f infra/compose/docker-compose.prod.yml logs --since=10m api | grep '${REQUEST_ID}'
  docker compose --env-file ${RUNTIME_ENV_FILE} -f docker-compose.yml -f infra/compose/docker-compose.prod.yml logs --since=10m web | grep '${REQUEST_ID}'
EOF

if [[ "${LOG_SEARCH_MODE}" == "docker" ]]; then
  echo "[INFO] Attempting Docker log search for request_id"
  if docker compose --env-file "${RUNTIME_ENV_FILE}" -f docker-compose.yml -f infra/compose/docker-compose.prod.yml logs --since=10m api 2>/dev/null | grep -q "${REQUEST_ID}"; then
    echo "[OK] request_id found in API Docker logs"
  else
    echo "[FAIL] request_id was not found in API Docker logs" >&2
    exit 1
  fi
else
  echo "[INFO] LOG_SEARCH_MODE=manual. Search logs in Loki/Grafana or external logging provider using REQUEST_ID above."
fi

echo "[OK] P3-04 request_id propagation validation completed"
