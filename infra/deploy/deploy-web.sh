#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

IMAGE_TAG="${1:-}"
IMAGE_REPOSITORY="${WEB_IMAGE_REPOSITORY:-ghcr.io/alexshcherb1173/vatranscribe-web}"
APP_DIR="/opt/vatranscribe/app"
ENV_FILE="/opt/vatranscribe/secrets/.env.runtime"
LEGACY_REGISTRY_COMPOSE="/opt/vatranscribe/deploy/docker-compose.registry.yml"
STATE_DIR="/opt/vatranscribe/deploy/state"
RELEASES_DIR="$STATE_DIR/web-releases"
LOCK_FILE="/tmp/vatranscribe-web-deploy.lock"
CONTAINER_NAME="vatranscribe-web"
HEALTH_URL="https://app.vatranscribe.ru/app/"
IMAGE_RELEASE_ROOT="/opt/vatranscribe/web-release"

if [[ ! "$IMAGE_TAG" =~ ^sha-[0-9a-f]{40}$ ]]; then
  echo "Invalid image tag: $IMAGE_TAG" >&2
  exit 64
fi

for required in \
  "$APP_DIR/docker-compose.yml" \
  "$APP_DIR/infra/compose/docker-compose.prod.yml" \
  "$APP_DIR/infra/docker/nginx.prod.conf.template" \
  "$ENV_FILE" \
  "$LEGACY_REGISTRY_COMPOSE"; do

  if [[ ! -e "$required" ]]; then
    echo "Required file is missing: $required" >&2
    exit 66
  fi
done

mkdir -p "$STATE_DIR" "$RELEASES_DIR"

exec 9>"$LOCK_FILE"

if ! flock -n 9; then
  echo "Another web deployment is already running." >&2
  exit 75
fi

export WEB_IMAGE_REPOSITORY="$IMAGE_REPOSITORY"
export WEB_IMAGE_TAG="$IMAGE_TAG"

TARGET_IMAGE="${IMAGE_REPOSITORY}:${IMAGE_TAG}"

compose_with_config() {
  local prod_compose="$1"
  local registry_compose="$2"
  local nginx_template="$3"

  shift 3

  WEB_NGINX_TEMPLATE_PATH="$nginx_template" \
    docker compose \
      -p vatranscribeweb \
      --project-directory "$APP_DIR" \
      --env-file "$ENV_FILE" \
      -f "$APP_DIR/docker-compose.yml" \
      -f "$prod_compose" \
      -f "$registry_compose" \
      "$@"
}

wait_for_web_health() {
  local attempt
  local status

  for attempt in $(seq 1 60); do
    status="$(
      docker inspect \
        --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
        "$CONTAINER_NAME" \
        2>/dev/null || true
    )"

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

validate_release_config() {
  local release_root="$1"
  local required

  for required in \
    infra/compose/docker-compose.prod.yml \
    infra/compose/docker-compose.registry.yml \
    infra/docker/nginx.prod.conf.template \
    infra/deploy/sync-nginx-certificates.sh; do

    if [[ ! -f "$release_root/$required" ]]; then
      echo "Immutable web release file is missing: $required" >&2
      return 1
    fi

    if [[ -L "$release_root/$required" ]]; then
      echo "Immutable web release file must not be a symlink: $required" >&2
      return 1
    fi
  done
}

extract_release_config() {
  local release_root="$1"
  local staging_root
  local container_id

  staging_root="${release_root}.tmp.$$"

  rm -rf -- "$staging_root"
  mkdir -p "$staging_root"

  container_id="$(docker create "$TARGET_IMAGE")"

  if ! docker cp \
      "${container_id}:${IMAGE_RELEASE_ROOT}/." \
      "$staging_root/"; then

    docker rm -f "$container_id" >/dev/null 2>&1 || true
    rm -rf -- "$staging_root"

    echo "Unable to extract immutable web deployment config." >&2
    return 1
  fi

  docker rm -f "$container_id" >/dev/null

  if ! validate_release_config "$staging_root"; then
    rm -rf -- "$staging_root"
    return 1
  fi

  rm -rf -- "$release_root"
  mv "$staging_root" "$release_root"
}

PREVIOUS_IMAGE_ID=""
ROLLBACK_TAG=""
PREVIOUS_RELEASE_ROOT=""

PREVIOUS_PROD_COMPOSE="$APP_DIR/infra/compose/docker-compose.prod.yml"
PREVIOUS_REGISTRY_COMPOSE="$LEGACY_REGISTRY_COMPOSE"
PREVIOUS_NGINX_TEMPLATE="$APP_DIR/infra/docker/nginx.prod.conf.template"

if docker inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  PREVIOUS_IMAGE_ID="$(
    docker inspect \
      --format '{{.Image}}' \
      "$CONTAINER_NAME"
  )"

  ROLLBACK_TAG="rollback-$(date -u +%Y%m%dT%H%M%SZ)"

  docker tag \
    "$PREVIOUS_IMAGE_ID" \
    "${IMAGE_REPOSITORY}:${ROLLBACK_TAG}"

  if [[ -s "$STATE_DIR/current-web-release-root" ]]; then
    IFS= read -r PREVIOUS_RELEASE_ROOT \
      < "$STATE_DIR/current-web-release-root"

    if [[ -n "$PREVIOUS_RELEASE_ROOT" ]] \
      && validate_release_config "$PREVIOUS_RELEASE_ROOT"; then

      PREVIOUS_PROD_COMPOSE="$PREVIOUS_RELEASE_ROOT/infra/compose/docker-compose.prod.yml"
      PREVIOUS_REGISTRY_COMPOSE="$PREVIOUS_RELEASE_ROOT/infra/compose/docker-compose.registry.yml"
      PREVIOUS_NGINX_TEMPLATE="$PREVIOUS_RELEASE_ROOT/infra/docker/nginx.prod.conf.template"
    else
      PREVIOUS_RELEASE_ROOT=""
    fi
  fi
fi

rollback() {
  local failure_line="$1"

  trap - ERR

  echo "Deployment failed near line $failure_line." >&2

  if [[ -n "$ROLLBACK_TAG" ]]; then
    echo "Rolling back to ${IMAGE_REPOSITORY}:${ROLLBACK_TAG}." >&2

    export WEB_IMAGE_TAG="$ROLLBACK_TAG"

    compose_with_config \
      "$PREVIOUS_PROD_COMPOSE" \
      "$PREVIOUS_REGISTRY_COMPOSE" \
      "$PREVIOUS_NGINX_TEMPLATE" \
      up -d \
      --no-deps \
      --force-recreate \
      --no-build \
      --pull never \
      web

    wait_for_web_health

    curl \
      --fail \
      --silent \
      --show-error \
      --location \
      --max-time 20 \
      --insecure \
      "$HEALTH_URL" \
      >/dev/null

    echo "Rollback completed." >&2
  else
    echo "Rollback image is unavailable." >&2
  fi

  exit 1
}

trap 'rollback "$LINENO"' ERR

echo "Pulling $TARGET_IMAGE"

docker pull "$TARGET_IMAGE"

TARGET_IMAGE_ID="$(
  docker image inspect \
    --format '{{.Id}}' \
    "$TARGET_IMAGE"
)"

EXPECTED_COMMIT="${IMAGE_TAG#sha-}"

IMAGE_REVISION="$(
  docker image inspect \
    --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' \
    "$TARGET_IMAGE"
)"

if [[ "$IMAGE_REVISION" != "$EXPECTED_COMMIT" ]]; then
  echo \
    "Image revision mismatch. Expected $EXPECTED_COMMIT, got $IMAGE_REVISION." \
    >&2

  false
fi

TARGET_RELEASE_ROOT="$RELEASES_DIR/$IMAGE_TAG"

extract_release_config "$TARGET_RELEASE_ROOT"

TARGET_PROD_COMPOSE="$TARGET_RELEASE_ROOT/infra/compose/docker-compose.prod.yml"
TARGET_REGISTRY_COMPOSE="$TARGET_RELEASE_ROOT/infra/compose/docker-compose.registry.yml"
TARGET_NGINX_TEMPLATE="$TARGET_RELEASE_ROOT/infra/docker/nginx.prod.conf.template"
TARGET_CERT_SYNC="$TARGET_RELEASE_ROOT/infra/deploy/sync-nginx-certificates.sh"

echo "Validating immutable web deployment configuration"

WEB_NGINX_TEMPLATE_PATH="$TARGET_NGINX_TEMPLATE" \
  docker compose \
    -p vatranscribeweb \
    --project-directory "$APP_DIR" \
    --env-file "$ENV_FILE" \
    -f "$APP_DIR/docker-compose.yml" \
    -f "$TARGET_PROD_COMPOSE" \
    -f "$TARGET_REGISTRY_COMPOSE" \
    config \
    >/dev/null

echo "Synchronizing runtime certificate volume"

WEB_NGINX_TEMPLATE_PATH="$TARGET_NGINX_TEMPLATE" \
PROJECT_ROOT="$APP_DIR" \
PROJECT_NAME="vatranscribeweb" \
RUNTIME_ENV_FILE="$ENV_FILE" \
COMPOSE_FILES="$APP_DIR/docker-compose.yml -f $TARGET_PROD_COMPOSE -f $TARGET_REGISTRY_COMPOSE" \
  bash "$TARGET_CERT_SYNC"

compose_with_config \
  "$TARGET_PROD_COMPOSE" \
  "$TARGET_REGISTRY_COMPOSE" \
  "$TARGET_NGINX_TEMPLATE" \
  up -d \
  --no-deps \
  --force-recreate \
  --no-build \
  --pull never \
  web

wait_for_web_health

RUNNING_IMAGE_ID="$(
  docker inspect \
    --format '{{.Image}}' \
    "$CONTAINER_NAME"
)"

if [[ "$RUNNING_IMAGE_ID" != "$TARGET_IMAGE_ID" ]]; then
  echo \
    "Running image mismatch. Expected $TARGET_IMAGE_ID, got $RUNNING_IMAGE_ID." \
    >&2

  false
fi

curl \
  --fail \
  --silent \
  --show-error \
  --location \
  --max-time 20 \
  --insecure \
  "$HEALTH_URL" \
  >/dev/null

printf '%s\n' \
  "$TARGET_IMAGE" \
  > "$STATE_DIR/current-web-image"

printf '%s\n' \
  "$RUNNING_IMAGE_ID" \
  > "$STATE_DIR/current-web-image-id"

printf '%s\n' \
  "$TARGET_RELEASE_ROOT" \
  > "$STATE_DIR/current-web-release-root"

printf '%s\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  > "$STATE_DIR/current-web-deployed-at"

trap - ERR

echo "Deployment successful: $TARGET_IMAGE"

docker ps \
  --filter "name=^/${CONTAINER_NAME}$" \
  --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
