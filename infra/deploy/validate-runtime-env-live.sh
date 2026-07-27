#!/usr/bin/env bash
set -euo pipefail

RUNTIME_ENV_FILE="${1:-${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}}"
EVIDENCE_FILE="${EVIDENCE_FILE:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

fail() { echo "[ERROR] $*" >&2; exit 1; }
warn() { echo "[WARN] $*" >&2; }
info() { echo "[INFO] $*" >&2; }

[[ -f "${RUNTIME_ENV_FILE}" ]] || fail "Runtime env file not found: ${RUNTIME_ENV_FILE}"
[[ -r "${RUNTIME_ENV_FILE}" ]] || fail "Runtime env file is not readable: ${RUNTIME_ENV_FILE}"

case "${RUNTIME_ENV_FILE}" in
  "${REPO_ROOT}"/*)
    fail "Runtime env file must not be inside the Git repository: ${RUNTIME_ENV_FILE}"
    ;;
esac

perms="$(stat -c '%a' "${RUNTIME_ENV_FILE}" 2>/dev/null || stat -f '%Lp' "${RUNTIME_ENV_FILE}" 2>/dev/null || echo unknown)"
if [[ "${perms}" != "unknown" ]]; then
  case "${perms}" in
    600|400) ;;
    *) warn "Runtime env file permissions are ${perms}; recommended: 600" ;;
  esac
fi

info "Running production secret validator for ${RUNTIME_ENV_FILE}"
"${SCRIPT_DIR}/validate-production-secrets.sh" "${RUNTIME_ENV_FILE}"

if [[ -n "${EVIDENCE_FILE}" ]]; then
  umask 077
  mkdir -p "$(dirname "${EVIDENCE_FILE}")"
  "${SCRIPT_DIR}/redact-runtime-env.sh" "${RUNTIME_ENV_FILE}" > "${EVIDENCE_FILE}"
  info "Redacted runtime evidence written: ${EVIDENCE_FILE}"
fi

info "Runtime secrets live validation completed"
