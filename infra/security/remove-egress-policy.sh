#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${1:-$SCRIPT_DIR/egress-policy.env}"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

CHAIN="${VATRANSCRIBE_EGRESS_CHAIN:-VATRANSCRIBE-EGRESS}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "This script must run as root on the Docker host." >&2
  exit 1
fi

while iptables -C DOCKER-USER -j "$CHAIN" 2>/dev/null; do
  iptables -D DOCKER-USER -j "$CHAIN"
done

# Also remove source-specific jumps if the apply script inserted them.
for container in "${VATRANSCRIBE_API_CONTAINER:-vatranscribe-api}" "${VATRANSCRIBE_WORKER_CONTAINER:-vatranscribe-worker}"; do
  ip="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$container" 2>/dev/null || true)"
  if [[ -n "$ip" ]]; then
    while iptables -C DOCKER-USER -s "$ip" -j "$CHAIN" 2>/dev/null; do
      iptables -D DOCKER-USER -s "$ip" -j "$CHAIN"
    done
  fi
done

iptables -F "$CHAIN" 2>/dev/null || true
iptables -X "$CHAIN" 2>/dev/null || true

echo "Removed VATranscribe egress policy chain: $CHAIN"
