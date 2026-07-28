#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

DEPLOY_SCRIPT="/opt/vatranscribe/deploy/deploy-web.sh"
ORIGINAL_COMMAND="${SSH_ORIGINAL_COMMAND:-}"

if [[ "$ORIGINAL_COMMAND" =~ ^deploy-web[[:space:]]+(sha-[0-9a-f]{40})$ ]]; then
  IMAGE_TAG="${BASH_REMATCH[1]}"
  logger -t vatranscribe-gha "web deploy requested: tag=${IMAGE_TAG} connection=${SSH_CONNECTION:-unknown}"
  exec "$DEPLOY_SCRIPT" "$IMAGE_TAG"
fi

echo "Command denied." >&2
logger -t vatranscribe-gha "denied command: ${ORIGINAL_COMMAND:-empty} connection=${SSH_CONNECTION:-unknown}"
exit 126
