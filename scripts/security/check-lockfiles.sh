#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

fail() {
  echo "[ERROR] $*" >&2
  exit 1
}

require_file() {
  local path="$1"
  [[ -f "$path" ]] || fail "Required file is missing: $path"
}

require_file "pyproject.toml"
require_file "package.json"
require_file "package-lock.json"
require_file "apps/web/package.json"
require_file "apps/marketing/package.json"
require_file "infra/docker/api.Dockerfile"
require_file "infra/docker/worker.Dockerfile"
require_file "infra/docker/web.Dockerfile"
require_file "infra/compose/docker-compose.prod.yml"

if git ls-files --others --exclude-standard | grep -E '(^|/)package-lock\.json$|(^|/)poetry\.lock$|(^|/)requirements.*\.txt$' >/dev/null; then
  echo "[WARN] Untracked dependency lock/manifests detected:" >&2
  git ls-files --others --exclude-standard | grep -E '(^|/)package-lock\.json$|(^|/)poetry\.lock$|(^|/)requirements.*\.txt$' >&2
  fail "Track or remove dependency lock/manifests before release."
fi

echo "[OK] Lockfile and manifest policy passed"
