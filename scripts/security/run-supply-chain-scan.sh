#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

REPORT_DIR="${SUPPLY_CHAIN_REPORT_DIR:-reports/security}"
mkdir -p "$REPORT_DIR"

run_or_warn() {
  local name="$1"
  shift
  echo "[SCAN] $name"
  if ! "$@"; then
    echo "[ERROR] $name failed" >&2
    return 1
  fi
}

bash scripts/security/check-lockfiles.sh

if command -v pip-audit >/dev/null 2>&1; then
  run_or_warn "pip-audit" pip-audit . --strict --progress-spinner off --timeout 60 --format json --output "$REPORT_DIR/pip-audit.json"
else
  echo "[WARN] pip-audit is not installed. Install with: python -m pip install pip-audit" >&2
fi

if command -v npm >/dev/null 2>&1; then
  run_or_warn "npm audit" npm audit --workspaces --audit-level=high --json > "$REPORT_DIR/npm-audit.json"
else
  echo "[WARN] npm is not installed" >&2
fi

if command -v trivy >/dev/null 2>&1; then
  run_or_warn "trivy fs" trivy fs --scanners vuln,config,secret --severity HIGH,CRITICAL --exit-code 1 --ignore-unfixed --format table . | tee "$REPORT_DIR/trivy-fs.txt"
else
  echo "[WARN] Trivy is not installed. See docs/security/supply-chain-security-scan.md" >&2
fi

if command -v gitleaks >/dev/null 2>&1; then
  run_or_warn "gitleaks" gitleaks dir . --config .gitleaks.local.toml --redact=100 --exit-code 1 --report-format json --report-path "$REPORT_DIR/gitleaks.json"
else
  echo "[WARN] Gitleaks is not installed. See docs/security/supply-chain-security-scan.md" >&2
fi

if command -v syft >/dev/null 2>&1; then
  run_or_warn "syft sbom" syft . -o spdx-json="$REPORT_DIR/sbom.spdx.json"
else
  echo "[INFO] Syft is optional for local runs. SBOM generation is documented and enabled in CI." >&2
fi

echo "[OK] Supply-chain scan completed"
