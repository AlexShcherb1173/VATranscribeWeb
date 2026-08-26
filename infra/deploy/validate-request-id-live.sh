#!/usr/bin/env bash
set -euo pipefail

# P3-04 request_id propagation and log-correlation validation.
#
# Production trust model:
# - the client may send X-Request-ID;
# - the edge proxy may replace it with a trusted edge-generated request_id;
# - the API returns the effective correlation ID;
# - log verification must search for the returned correlation ID.
#
# Do not print secrets.

RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
REQUEST_ID_HEADER="${REQUEST_ID_HEADER:-X-Request-ID}"
SMOKE_TIMEOUT_SECONDS="${SMOKE_TIMEOUT_SECONDS:-10}"
LOG_SEARCH_MODE="${LOG_SEARCH_MODE:-manual}"
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
DOCKER_LOG_SINCE="${DOCKER_LOG_SINCE:-10m}"

if [[ -f "${RUNTIME_ENV_FILE}" ]]; then
  set -a
  # shellcheck source=/dev/null
  . "${RUNTIME_ENV_FILE}"
  set +a
fi

API_URL="${PUBLIC_API_ORIGIN:-https://api.vatranscribe.ru}"
CLIENT_REQUEST_ID="${REQUEST_ID:-p3-04-$(date -u +%Y%m%dT%H%M%SZ)-$$}"

HEADERS_FILE="$(mktemp)"
BODY_FILE="$(mktemp)"
API_LOG_FILE="$(mktemp)"
WEB_LOG_FILE="$(mktemp)"

cleanup() {
  rm -f \
    "${HEADERS_FILE}" \
    "${BODY_FILE}" \
    "${API_LOG_FILE}" \
    "${WEB_LOG_FILE}"
}

trap cleanup EXIT

TARGET_URL="${API_URL%/}/api/v1/health/live"

echo "[INFO] Sending ${REQUEST_ID_HEADER} to ${TARGET_URL}"

status="$(
  curl \
    --silent \
    --show-error \
    --max-time "${SMOKE_TIMEOUT_SECONDS}" \
    --header "${REQUEST_ID_HEADER}: ${CLIENT_REQUEST_ID}" \
    --dump-header "${HEADERS_FILE}" \
    --output "${BODY_FILE}" \
    --write-out '%{http_code}' \
    "${TARGET_URL}"
)"

if [[ "${status}" != "200" ]]; then
  echo "[FAIL] API live returned HTTP ${status}" >&2
  cat "${BODY_FILE}" >&2 || true
  exit 1
fi

CORRELATION_REQUEST_ID="$(
  tr -d '\r' < "${HEADERS_FILE}" |
    awk -v wanted="${REQUEST_ID_HEADER}" '
      {
        line = $0
        separator = index(line, ":")

        if (separator == 0) {
          next
        }

        name = substr(line, 1, separator - 1)
        value = substr(line, separator + 1)

        gsub(/^[[:space:]]+|[[:space:]]+$/, "", name)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)

        if (tolower(name) == tolower(wanted)) {
          print value
          exit
        }
      }
    '
)"

if [[ -z "${CORRELATION_REQUEST_ID}" ]]; then
  echo "[FAIL] Response does not contain ${REQUEST_ID_HEADER}" >&2
  cat "${HEADERS_FILE}" >&2 || true
  exit 1
fi

if [[ "${CORRELATION_REQUEST_ID}" == "${CLIENT_REQUEST_ID}" ]]; then
  REQUEST_ID_MODEL="CLIENT_ID_PRESERVED"
else
  REQUEST_ID_MODEL="EDGE_GENERATED"
fi

echo "[OK] Response contains effective ${REQUEST_ID_HEADER}"
echo "CLIENT_REQUEST_ID=${CLIENT_REQUEST_ID}"
echo "CORRELATION_REQUEST_ID=${CORRELATION_REQUEST_ID}"
echo "REQUEST_ID_MODEL=${REQUEST_ID_MODEL}"

cat <<EOF
[INFO] Effective request ID log-search marker:
REQUEST_ID=${CORRELATION_REQUEST_ID}

Manual Loki/Grafana query examples:
  {service="api"} |= "${CORRELATION_REQUEST_ID}"
  {container="vatranscribe-api"} |= "${CORRELATION_REQUEST_ID}"

Manual Docker fallback:
  Search the current api and web container logs for:
  ${CORRELATION_REQUEST_ID}
EOF

if [[ "${LOG_SEARCH_MODE}" == "docker" ]]; then
  echo "[INFO] Attempting Docker log correlation using returned request_id"

  mapfile -t API_CONTAINER_IDS < <(
    docker ps \
      --filter "label=com.docker.compose.project=${PROJECT_NAME}" \
      --filter "label=com.docker.compose.service=api" \
      --format '{{.ID}}'
  )

  mapfile -t WEB_CONTAINER_IDS < <(
    docker ps \
      --filter "label=com.docker.compose.project=${PROJECT_NAME}" \
      --filter "label=com.docker.compose.service=web" \
      --format '{{.ID}}'
  )

  if [[ "${#API_CONTAINER_IDS[@]}" -ne 1 ]]; then
    echo "[FAIL] Expected exactly one running API container, found ${#API_CONTAINER_IDS[@]}" >&2
    exit 1
  fi

  if [[ "${#WEB_CONTAINER_IDS[@]}" -ne 1 ]]; then
    echo "[FAIL] Expected exactly one running web container, found ${#WEB_CONTAINER_IDS[@]}" >&2
    exit 1
  fi

  if ! docker logs \
    --since "${DOCKER_LOG_SINCE}" \
    "${API_CONTAINER_IDS[0]}" \
    > "${API_LOG_FILE}" \
    2>&1
  then
    echo "[FAIL] Unable to read API Docker logs" >&2
    exit 1
  fi

  if ! docker logs \
    --since "${DOCKER_LOG_SINCE}" \
    "${WEB_CONTAINER_IDS[0]}" \
    > "${WEB_LOG_FILE}" \
    2>&1
  then
    echo "[FAIL] Unable to read web Docker logs" >&2
    exit 1
  fi

  if grep -F \
    -- "${CORRELATION_REQUEST_ID}" \
    "${API_LOG_FILE}" \
    >/dev/null
  then
    echo "[OK] request_id found in API Docker logs"
  else
    echo "[FAIL] returned request_id was not found in API Docker logs" >&2
    exit 1
  fi

  if grep -F \
    -- "${CORRELATION_REQUEST_ID}" \
    "${WEB_LOG_FILE}" \
    >/dev/null
  then
    echo "[OK] request_id found in Nginx Docker logs"
  else
    echo "[FAIL] returned request_id was not found in Nginx Docker logs" >&2
    exit 1
  fi

  echo "REQUEST_ID_DOCKER_CORRELATION_OK"
else
  echo "[INFO] LOG_SEARCH_MODE=manual. Search external logs using CORRELATION_REQUEST_ID above."
fi

echo "REQUEST_ID_LIVE_VERIFICATION_OK correlation_id=${CORRELATION_REQUEST_ID} model=${REQUEST_ID_MODEL}"
echo "[OK] P3-04 request_id propagation validation completed"
