#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

IMAGE_TAG="${1:-}"
IMAGE_REPOSITORY="${WEB_IMAGE_REPOSITORY:-ghcr.io/alexshcherb1173/vatranscribe-web}"
APP_DIR="/opt/vatranscribe/app"
ENV_FILE="/opt/vatranscribe/secrets/.env.runtime"
REGISTRY_COMPOSE="/opt/vatranscribe/deploy/docker-compose.registry.yml"
STATE_DIR="/opt/vatranscribe/deploy/state"
LOCK_FILE="/tmp/vatranscribe-web-deploy.lock"
CONTAINER_NAME="vatranscribe-web"
HEALTH_URL="https://app.vatranscribe.ru/app/"

if [[ ! "$IMAGE_TAG" =~ ^sha-[0-9a-f]{40}$ ]]; then
  echo "Invalid image tag: $IMAGE_TAG" >&2
  exit 64
fi

for required in \
  "$APP_DIR/docker-compose.yml" \
  "$APP_DIR/infra/compose/docker-compose.prod.yml" \
  "$ENV_FILE" \
  "$REGISTRY_COMPOSE"; do
  if [[ ! -e "$required" ]]; then
    echo "Required file is missing: $required" >&2
    exit 66
  fi
done

mkdir -p "$STATE_DIR"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Another web deployment is already running." >&2
  exit 75
fi

export WEB_IMAGE_REPOSITORY="$IMAGE_REPOSITORY"
export WEB_IMAGE_TAG="$IMAGE_TAG"
TARGET_IMAGE="${IMAGE_REPOSITORY}:${IMAGE_TAG}"

compose() {
  docker compose \
    -p vatranscribeweb \
    --env-file "$ENV_FILE" \
    -f "$APP_DIR/docker-compose.yml" \
    -f "$APP_DIR/infra/compose/docker-compose.prod.yml" \
    -f "$REGISTRY_COMPOSE" \
    "$@"
}

wait_for_web_health() {
  local attempt status
  for attempt in $(seq 1 60); do
    status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$CONTAINER_NAME" 2>/dev/null || true)"
    case "$status" in
      healthy)
        return 0
        ;;
      exited|dead|unhealthy)
        echo "Container entered terminal state: $status" >&2
        return 1
        ;;
    esac
    sleep 2
  done

  echo "Timed out waiting for container health." >&2
  return 1
}

PREVIOUS_IMAGE_ID=""
ROLLBACK_TAG=""

if docker inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  PREVIOUS_IMAGE_ID="$(docker inspect --format '{{.Image}}' "$CONTAINER_NAME")"
  ROLLBACK_TAG="rollback-$(date -u +%Y%m%dT%H%M%SZ)"
  docker tag "$PREVIOUS_IMAGE_ID" "${IMAGE_REPOSITORY}:${ROLLBACK_TAG}"
fi

rollback() {
  local failure_line="$1"
  trap - ERR

  echo "Deployment failed near line $failure_line." >&2

  if [[ -n "$ROLLBACK_TAG" ]]; then
    echo "Rolling back to ${IMAGE_REPOSITORY}:${ROLLBACK_TAG}." >&2
    export WEB_IMAGE_TAG="$ROLLBACK_TAG"
    compose up -d --no-deps --force-recreate --no-build --pull never web
    wait_for_web_health
    curl --fail --silent --show-error --location --max-time 20 --insecure "$HEALTH_URL" >/dev/null
    echo "Rollback completed." >&2
  else
    echo "Rollback image is unavailable." >&2
  fi

  exit 1
}

trap 'rollback "$LINENO"' ERR

echo "Pulling $TARGET_IMAGE"
docker pull "$TARGET_IMAGE"

TARGET_IMAGE_ID="$(docker image inspect --format '{{.Id}}' "$TARGET_IMAGE")"

echo "Synchronizing runtime certificate volume"

PROJECT_ROOT="$APP_DIR" \
PROJECT_NAME="vatranscribeweb" \
RUNTIME_ENV_FILE="$ENV_FILE" \
COMPOSE_FILES="$APP_DIR/docker-compose.yml -f $APP_DIR/infra/compose/docker-compose.prod.yml -f $REGISTRY_COMPOSE" \
  bash "$APP_DIR/infra/deploy/sync-nginx-certificates.sh"

compose up -d --no-deps --force-recreate --no-build --pull never web
wait_for_web_health

RUNNING_IMAGE_ID="$(docker inspect --format '{{.Image}}' "$CONTAINER_NAME")"
if [[ "$RUNNING_IMAGE_ID" != "$TARGET_IMAGE_ID" ]]; then
  echo "Running image mismatch. Expected $TARGET_IMAGE_ID, got $RUNNING_IMAGE_ID." >&2
  false
fi

curl --fail --silent --show-error --location --max-time 20 --insecure "$HEALTH_URL" >/dev/null

printf '%s\n' "$TARGET_IMAGE" > "$STATE_DIR/current-web-image"
printf '%s\n' "$RUNNING_IMAGE_ID" > "$STATE_DIR/current-web-image-id"
printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$STATE_DIR/current-web-deployed-at"

trap - ERR

echo "Deployment successful: $TARGET_IMAGE"
docker ps --filter "name=^/${CONTAINER_NAME}$" --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
