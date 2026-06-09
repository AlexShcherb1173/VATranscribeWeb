#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${1:-$SCRIPT_DIR/egress-policy.env}"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

API_CONTAINER="${VATRANSCRIBE_API_CONTAINER:-vatranscribe-api}"
WORKER_CONTAINER="${VATRANSCRIBE_WORKER_CONTAINER:-vatranscribe-worker}"
DB_CONTAINER="${VATRANSCRIBE_DB_CONTAINER:-vatranscribe-db}"
REDIS_CONTAINER="${VATRANSCRIBE_REDIS_CONTAINER:-vatranscribe-redis}"
CHAIN="${VATRANSCRIBE_EGRESS_CHAIN:-VATRANSCRIBE-EGRESS}"
STRICT="${VATRANSCRIBE_EGRESS_STRICT:-true}"
LOG_DENIES="${VATRANSCRIBE_EGRESS_LOG_DENIES:-false}"

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "This script must run as root on the Docker host." >&2
    exit 1
  fi
}

container_ip() {
  local name="$1"
  docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$name"
}

add_once() {
  if ! iptables -C "$@" 2>/dev/null; then
    iptables -A "$@"
  fi
}

insert_once() {
  if ! iptables -C "$@" 2>/dev/null; then
    iptables -I "$@"
  fi
}

private_blocks=(
  "127.0.0.0/8"
  "10.0.0.0/8"
  "172.16.0.0/12"
  "192.168.0.0/16"
  "169.254.0.0/16"
  "169.254.169.254/32"
  "100.64.0.0/10"
  "0.0.0.0/8"
  "240.0.0.0/4"
)

require_root

API_IP="$(container_ip "$API_CONTAINER")"
WORKER_IP="$(container_ip "$WORKER_CONTAINER")"
DB_IP="$(container_ip "$DB_CONTAINER")"
REDIS_IP="$(container_ip "$REDIS_CONTAINER")"

if [[ -z "$API_IP" || -z "$WORKER_IP" || -z "$DB_IP" || -z "$REDIS_IP" ]]; then
  echo "Failed to resolve one or more container IPs." >&2
  exit 1
fi

iptables -N "$CHAIN" 2>/dev/null || true
iptables -F "$CHAIN"

# Keep existing connections stable.
add_once "$CHAIN" -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN

for src in "$API_IP" "$WORKER_IP"; do
  # Required internal dependencies.
  add_once "$CHAIN" -s "$src" -d "$DB_IP" -p tcp --dport 5432 -j RETURN
  add_once "$CHAIN" -s "$src" -d "$REDIS_IP" -p tcp --dport 6379 -j RETURN

  # Block private, loopback, link-local and metadata egress for SSRF defense-in-depth.
  for cidr in "${private_blocks[@]}"; do
    if [[ "$LOG_DENIES" == "true" ]]; then
      add_once "$CHAIN" -s "$src" -d "$cidr" -j LOG --log-prefix "vatranscribe-egress-deny " --log-level 4
    fi
    add_once "$CHAIN" -s "$src" -d "$cidr" -j REJECT
  done

  # yt-dlp and normal external integrations should use public HTTP/HTTPS only.
  add_once "$CHAIN" -s "$src" -p tcp -m multiport --dports 80,443 -j RETURN

  if [[ "$STRICT" == "true" ]]; then
    if [[ "$LOG_DENIES" == "true" ]]; then
      add_once "$CHAIN" -s "$src" -j LOG --log-prefix "vatranscribe-egress-strict-deny " --log-level 4
    fi
    add_once "$CHAIN" -s "$src" -j REJECT
  else
    add_once "$CHAIN" -s "$src" -j RETURN
  fi
done

insert_once DOCKER-USER -s "$API_IP" -j "$CHAIN"
insert_once DOCKER-USER -s "$WORKER_IP" -j "$CHAIN"

cat <<EOT
Applied VATranscribe egress policy:
  chain: $CHAIN
  api: $API_CONTAINER ($API_IP)
  worker: $WORKER_CONTAINER ($WORKER_IP)
  db allowed: $DB_CONTAINER ($DB_IP):5432
  redis allowed: $REDIS_CONTAINER ($REDIS_IP):6379
  strict: $STRICT
EOT
