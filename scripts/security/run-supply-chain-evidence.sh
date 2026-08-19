#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
EVIDENCE_ROOT="${SUPPLY_CHAIN_EVIDENCE_DIR:-reports/security/supply-chain-evidence}"
EVIDENCE_DIR="${EVIDENCE_ROOT}/${TIMESTAMP}"
RAW_DIR="${EVIDENCE_DIR}/raw"
SUMMARY_FILE="${EVIDENCE_DIR}/supply-chain-evidence.raw.md"
SANITIZED_FILE="${EVIDENCE_DIR}/supply-chain-evidence.sanitized.md"
TRIAGE_FILE="${EVIDENCE_DIR}/vulnerability-triage-high-critical.md"

mkdir -p "$RAW_DIR"

status_of() {
  local code="$1"
  if [ "$code" -eq 0 ]; then
    printf "PASS"
  else
    printf "FAIL"
  fi
}

run_capture() {
  local name="$1"
  local logfile="$2"
  shift 2

  echo "[SCAN] $name"
  set +e
  "$@" >"$logfile" 2>&1
  local code=$?
  set -e
  echo "$code"
}

run_capture_with_stdout_json() {
  local name="$1"
  local outfile="$2"
  shift 2

  echo "[SCAN] $name"
  set +e
  "$@" >"$outfile" 2>"${outfile}.stderr"
  local code=$?
  set -e
  echo "$code"
}

required_tool_status() {
  local tool="$1"
  if command -v "$tool" >/dev/null 2>&1; then
    printf "available"
  else
    printf "missing"
  fi
}

PIP_AUDIT_STATUS="missing"
NPM_AUDIT_STATUS="missing"
TRIVY_STATUS="missing"
GITLEAKS_STATUS="missing"
SYFT_STATUS="missing"
LOCKFILES_STATUS="not-run"

LOCKFILES_EXIT="$(run_capture "lockfile policy" "${RAW_DIR}/check-lockfiles.log" bash scripts/security/check-lockfiles.sh)"
LOCKFILES_STATUS="$(status_of "$LOCKFILES_EXIT")"

if command -v pip-audit >/dev/null 2>&1; then
  set +e
  pip-audit . --strict --progress-spinner off --timeout 60 --format json --output "${RAW_DIR}/pip-audit.json" >"${RAW_DIR}/pip-audit.log" 2>&1
  PIP_AUDIT_EXIT=$?
  set -e
  PIP_AUDIT_STATUS="$(status_of "$PIP_AUDIT_EXIT")"
else
  PIP_AUDIT_EXIT=127
  echo "pip-audit not installed" >"${RAW_DIR}/pip-audit.log"
fi

if command -v npm >/dev/null 2>&1; then
  NPM_AUDIT_EXIT="$(run_capture_with_stdout_json "npm audit" "${RAW_DIR}/npm-audit.json" npm audit --workspaces --audit-level=high --json)"
  NPM_AUDIT_STATUS="$(status_of "$NPM_AUDIT_EXIT")"
else
  NPM_AUDIT_EXIT=127
  echo "npm not installed" >"${RAW_DIR}/npm-audit.json"
fi

if command -v trivy >/dev/null 2>&1; then
  set +e
  trivy fs --timeout 30m --scanners vuln,misconfig,secret --severity HIGH,CRITICAL --exit-code 1 --ignore-unfixed --skip-dirs "**/node_modules" --format json --output "${RAW_DIR}/trivy-fs.json" . >"${RAW_DIR}/trivy-fs.log" 2>&1
  TRIVY_EXIT=$?
  set -e
  TRIVY_STATUS="$(status_of "$TRIVY_EXIT")"
else
  TRIVY_EXIT=127
  echo "trivy not installed" >"${RAW_DIR}/trivy-fs.log"
fi

if command -v gitleaks >/dev/null 2>&1; then
  set +e
  gitleaks dir . --config .gitleaks.local.toml --redact=100 --exit-code 1 --report-format json --report-path "${RAW_DIR}/gitleaks.json" >"${RAW_DIR}/gitleaks.log" 2>&1
  GITLEAKS_EXIT=$?
  set -e
  GITLEAKS_STATUS="$(status_of "$GITLEAKS_EXIT")"
else
  GITLEAKS_EXIT=127
  echo "gitleaks not installed" >"${RAW_DIR}/gitleaks.log"
fi

if command -v syft >/dev/null 2>&1; then
  set +e
  syft . -o "spdx-json=${RAW_DIR}/sbom.spdx.json" >"${RAW_DIR}/syft.log" 2>&1
  SYFT_EXIT=$?
  set -e
  SYFT_STATUS="$(status_of "$SYFT_EXIT")"
else
  SYFT_EXIT=127
  echo "syft not installed" >"${RAW_DIR}/syft.log"
fi

RELEASE_DECISION="PASS"
if [ "$LOCKFILES_EXIT" -ne 0 ] || [ "$PIP_AUDIT_EXIT" -ne 0 ] || [ "$NPM_AUDIT_EXIT" -ne 0 ] || [ "$TRIVY_EXIT" -ne 0 ] || [ "$GITLEAKS_EXIT" -ne 0 ] || [ "$SYFT_EXIT" -ne 0 ]; then
  RELEASE_DECISION="BLOCKED_OR_REQUIRES_TRIAGE"
fi

cat >"$SUMMARY_FILE" <<EOF_SUMMARY
# P3-07 Supply-chain evidence

Generated at UTC: ${TIMESTAMP}
Git commit: $(git rev-parse HEAD 2>/dev/null || echo unknown)
Git branch: $(git branch --show-current 2>/dev/null || echo unknown)
Evidence directory: ${EVIDENCE_DIR}

## Tool availability

| Tool | Status |
|---|---|
| pip-audit | $(required_tool_status pip-audit) |
| npm | $(required_tool_status npm) |
| Trivy | $(required_tool_status trivy) |
| Gitleaks | $(required_tool_status gitleaks) |
| Syft | $(required_tool_status syft) |

## Scan results

| Gate | Status | Exit code | Raw report |
|---|---:|---:|---|
| Lockfile policy | ${LOCKFILES_STATUS} | ${LOCKFILES_EXIT} | raw/check-lockfiles.log |
| pip-audit | ${PIP_AUDIT_STATUS} | ${PIP_AUDIT_EXIT} | raw/pip-audit.json |
| npm audit | ${NPM_AUDIT_STATUS} | ${NPM_AUDIT_EXIT} | raw/npm-audit.json |
| Trivy filesystem/config/secret | ${TRIVY_STATUS} | ${TRIVY_EXIT} | raw/trivy-fs.json |
| Gitleaks secret scan | ${GITLEAKS_STATUS} | ${GITLEAKS_EXIT} | raw/gitleaks.json |
| Syft SBOM | ${SYFT_STATUS} | ${SYFT_EXIT} | raw/sbom.spdx.json |

## Release decision

Release decision: ${RELEASE_DECISION}

Critical and high findings block production release until fixed or explicitly triaged by the release owner. Medium findings require manual review. Low findings may be accepted with documented review.

## Secret handling notice

DO NOT commit raw scan reports, SBOM files, private registry URLs, tokens, credentials, runtime env files, or unreviewed Gitleaks findings to the repository.
EOF_SUMMARY

cat >"$TRIAGE_FILE" <<'EOF_TRIAGE'
# High/Critical vulnerability triage

Use this file for release-owner review. Store the completed copy outside Git unless it is fully sanitized.

| Finding | Scanner | Package/image/file | Severity | Reachability | User/data exposure | Fix/mitigation | Decision | Owner | Review date | Expiry date |
|---|---|---|---|---|---|---|---|---|---|---|
| _fill locally_ | _pip-audit/npm audit/Trivy/Gitleaks_ | _fill locally_ | _Critical/High_ | _yes/no/unknown_ | _yes/no/unknown_ | _fix version or mitigation_ | _fix/block/temporary exception_ | _owner_ | _YYYY-MM-DD_ | _YYYY-MM-DD or N/A_ |

Critical findings require a fix before public release unless the release owner records a formal no-exposure decision. High findings block release unless fixed or covered by a dated temporary exception.
EOF_TRIAGE

bash scripts/security/redact-supply-chain-evidence.sh "$SUMMARY_FILE" "$SANITIZED_FILE"

chmod 600 "$SUMMARY_FILE" "$SANITIZED_FILE" "$TRIAGE_FILE" 2>/dev/null || true

echo "[OK] Supply-chain evidence run completed"
echo "[OK] Raw evidence directory: ${RAW_DIR}"
echo "[OK] Sanitized summary: ${SANITIZED_FILE}"
echo "[OK] Triage template: ${TRIAGE_FILE}"

if [ "$RELEASE_DECISION" != "PASS" ]; then
  echo "[BLOCKED] Supply-chain release gate requires triage. See ${TRIAGE_FILE}" >&2
  exit 1
fi
