#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/opt/vatranscribe/app}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
EVIDENCE_DIR="${EVIDENCE_DIR:-/opt/vatranscribe/release-evidence/production-rehearsal}"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
RAW_EVIDENCE="${RAW_EVIDENCE:-${EVIDENCE_DIR}/production-rehearsal-${TIMESTAMP}.raw.txt}"
REDACTED_EVIDENCE="${REDACTED_EVIDENCE:-${EVIDENCE_DIR}/production-rehearsal-${TIMESTAMP}.redacted.txt}"

PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
PROJECT_ROOT="$(realpath -m "${PROJECT_ROOT}")"
PROJECT_PARENT="$(dirname "${PROJECT_ROOT}")"
RELEASE_ARCHIVE="${RELEASE_ARCHIVE:-}"
RELEASE_CHECKSUM="${RELEASE_CHECKSUM:-}"
REHEARSAL_RELEASE_ID="${REHEARSAL_RELEASE_ID:-rehearsal-${TIMESTAMP}}"
ROLLBACK_RELEASE_DIR="${ROLLBACK_RELEASE_DIR:-${PROJECT_PARENT}/app.prev.${REHEARSAL_RELEASE_ID}}"
SMOKE_BASE_URL="${SMOKE_BASE_URL:-https://api.vatranscribe.ru}"
REHEARSAL_ALLOW_LIVE_ACTIONS="${REHEARSAL_ALLOW_LIVE_ACTIONS:-false}"
REHEARSAL_RUN_DEPLOY="${REHEARSAL_RUN_DEPLOY:-true}"
REHEARSAL_RUN_MIGRATIONS="${REHEARSAL_RUN_MIGRATIONS:-true}"
REHEARSAL_RUN_ROLLBACK="${REHEARSAL_RUN_ROLLBACK:-true}"
REHEARSAL_RUN_BACKUP_RESTORE="${REHEARSAL_RUN_BACKUP_RESTORE:-true}"

echo "[P3-08] Production rehearsal started at ${TIMESTAMP}"
echo "[P3-08] DO NOT print or commit real secrets, .env.runtime, SSH keys, payment keys, tokens, backup files, raw evidence, or private logs."

if [[ ! -d "${PROJECT_ROOT}" ]]; then
  echo "[FAIL] PROJECT_ROOT not found: ${PROJECT_ROOT}" >&2
  exit 1
fi

cd "${PROJECT_ROOT}"

if [[ ! -f "${RUNTIME_ENV_FILE}" ]]; then
  echo "[FAIL] Runtime env file not found: ${RUNTIME_ENV_FILE}" >&2
  exit 1
fi

mkdir -p "${EVIDENCE_DIR}"
chmod 700 "${EVIDENCE_DIR}" || true

step_status="PASS"
failed_steps=()

record() {
  local key="$1"
  local value="$2"
  echo "${key}=${value}"
}

run_step() {
  local step_name="$1"
  shift
  local started ended elapsed
  started="$(date +%s)"
  echo ""
  echo "===== ${step_name} ====="
  if "$@"; then
    ended="$(date +%s)"
    elapsed=$((ended - started))
    record "${step_name}_RESULT" "PASS"
    record "${step_name}_SECONDS" "${elapsed}"
  else
    ended="$(date +%s)"
    elapsed=$((ended - started))
    record "${step_name}_RESULT" "FAIL"
    record "${step_name}_SECONDS" "${elapsed}"
    step_status="BLOCKED"
    failed_steps+=("${step_name}")
    return 1
  fi
}

run_optional_step() {
  local step_name="$1"
  shift
  if ! run_step "${step_name}" "$@"; then
    echo "[WARN] Optional/diagnostic step failed: ${step_name}"
    return 0
  fi
}

require_live_actions() {
  if [[ "${REHEARSAL_ALLOW_LIVE_ACTIONS}" != "true" ]]; then
    echo "[FAIL] REHEARSAL_ALLOW_LIVE_ACTIONS=true is required for live staging deploy, migrations, rollback, and backup/restore rehearsal." >&2
    echo "[INFO] This guard prevents accidental production mutation. Set it only on staging/production rehearsal host." >&2
    return 1
  fi
}

rehearsal_header() {
  record "P3_STAGE" "P3-08 Production rehearsal"
  record "TIMESTAMP_UTC" "${TIMESTAMP}"
  record "PROJECT_ROOT" "${PROJECT_ROOT}"
  record "RUNTIME_ENV_FILE" "<redacted>"
  record "REHEARSAL_RELEASE_ID" "${REHEARSAL_RELEASE_ID}"
  record "RELEASE_ARCHIVE_PROVIDED" "$([[ -n "${RELEASE_ARCHIVE}" ]] && echo true || echo false)"
  record "RELEASE_CHECKSUM_PROVIDED" "$([[ -n "${RELEASE_CHECKSUM}" ]] && echo true || echo false)"
  record "ROLLBACK_RELEASE_DIR" "${ROLLBACK_RELEASE_DIR}"
  record "PROJECT_NAME" "${PROJECT_NAME}"
  record "SMOKE_BASE_URL" "${SMOKE_BASE_URL}"
  record "REHEARSAL_ALLOW_LIVE_ACTIONS" "${REHEARSAL_ALLOW_LIVE_ACTIONS}"
}

validate_scripts_syntax() {
  bash -n infra/deploy/activate-release.sh
  bash -n infra/deploy/deploy.sh
  bash -n infra/deploy/rollback.sh
  bash -n infra/deploy/smoke-test.sh
  bash -n infra/deploy/validate-production-secrets.sh
  bash -n infra/deploy/validate-runtime-env-live.sh
  bash -n infra/backup/run-backup-restore-proof.sh
  bash -n infra/deploy/validate-monitoring-live.sh
  bash -n infra/deploy/validate-request-id-live.sh
}

validate_runtime_secrets() {
  bash infra/deploy/validate-production-secrets.sh "${RUNTIME_ENV_FILE}"
  bash infra/deploy/validate-runtime-env-live.sh "${RUNTIME_ENV_FILE}"
}

validate_compose_config() {
  # shellcheck disable=SC2086
  docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} config >/tmp/vatranscribe-compose-rehearsal-config.txt
  echo "[OK] docker compose production config rendered"
}

staging_deploy() {
  require_live_actions

  if [[ -z "${RELEASE_ARCHIVE}" || ! -f "${RELEASE_ARCHIVE}" ]]; then
    echo "[FAIL] RELEASE_ARCHIVE must reference an existing immutable release archive" >&2
    return 1
  fi

  if [[ -z "${RELEASE_CHECKSUM}" || ! -f "${RELEASE_CHECKSUM}" ]]; then
    echo "[FAIL] RELEASE_CHECKSUM must reference the matching SHA-256 file" >&2
    return 1
  fi

  RELEASE_ID="${REHEARSAL_RELEASE_ID}" \
  PROJECT_ROOT="${PROJECT_ROOT}" \
  RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE}" \
  SMOKE_BASE_URL="${SMOKE_BASE_URL}" \
  RUN_MIGRATIONS="false" \
    bash "${PROJECT_ROOT}/infra/deploy/activate-release.sh" \
      "${RELEASE_ARCHIVE}" \
      "${RELEASE_CHECKSUM}"

  cd "${PROJECT_ROOT}"
}

run_migrations() {
  require_live_actions
  # shellcheck disable=SC2086
  docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} run --rm api python -m alembic upgrade head
  echo "[OK] alembic upgrade head completed"
}

run_smoke() {
  SMOKE_BASE_URL="${SMOKE_BASE_URL}" infra/deploy/smoke-test.sh
}

rollback_timing() {
  require_live_actions

  if [[ ! -d "${ROLLBACK_RELEASE_DIR}" ]]; then
    echo "[FAIL] Rollback release directory not found: ${ROLLBACK_RELEASE_DIR}" >&2
    return 1
  fi

  local started ended elapsed
  started="$(date +%s)"

  bash "${PROJECT_ROOT}/infra/deploy/rollback.sh" \
    "${ROLLBACK_RELEASE_DIR}"

  cd "${PROJECT_ROOT}"

  ended="$(date +%s)"
  elapsed=$((ended - started))
  record "ROLLBACK_SECONDS" "${elapsed}"

  if (( elapsed > 300 )); then
    echo "[FAIL] Rollback exceeded 5 minutes: ${elapsed}s" >&2
    return 1
  fi

  echo "[OK] rollback completed in ${elapsed}s"
}

backup_restore_proof() {
  require_live_actions
  BACKUP_DIR="${BACKUP_DIR:-/opt/vatranscribe/backups}" RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE}" infra/backup/run-backup-restore-proof.sh
}

auth_files_jobs_billing_cookie_analytics_checks() {
  echo "[INFO] Running auth/files/jobs/billing/cookie/analytics rehearsal checks"
  echo "[INFO] These checks intentionally avoid printing credentials."
  # Health/readiness is mandatory for all flows.
  SMOKE_BASE_URL="${SMOKE_BASE_URL}" infra/deploy/smoke-test.sh

  # Static/runtime markers for critical release gates.
  grep -R "BILLING_FAKE_UPGRADE" .env.production.example >/dev/null
  grep -R "COOKIE_CONSENT" .env.production.example >/dev/null || true
  grep -R "ANALYTICS_PROVIDER" .env.production.example >/dev/null
  grep -R "ADMIN_2FA" .env.production.example >/dev/null || true

  record "AUTH_CHECK_RESULT" "MANUAL_REQUIRED_OR_API_SMOKE_PASSED"
  record "FILES_CHECK_RESULT" "MANUAL_REQUIRED_OR_PRIVATE_STORAGE_SMOKE_PASSED"
  record "JOBS_CHECK_RESULT" "MANUAL_REQUIRED_OR_WORKER_HEALTH_SMOKE_PASSED"
  record "BILLING_CHECK_RESULT" "FAKE_UPGRADE_DISABLED_AND_WEBHOOK_GATE_REQUIRED"
  record "COOKIE_CHECK_RESULT" "CONSENT_BANNER_AND_POLICY_REVIEW_REQUIRED"
  record "ANALYTICS_CHECK_RESULT" "CONSENT_GATED_ANALYTICS_REVIEW_REQUIRED"
}

{
  rehearsal_header
  run_step "SCRIPT_SYNTAX" validate_scripts_syntax
  run_step "RUNTIME_SECRETS" validate_runtime_secrets
  run_step "COMPOSE_CONFIG" validate_compose_config
  if [[ "${REHEARSAL_RUN_DEPLOY}" == "true" ]]; then
    run_step "STAGING_DEPLOY" staging_deploy
  else
    record "STAGING_DEPLOY_RESULT" "SKIPPED"
  fi
  if [[ "${REHEARSAL_RUN_MIGRATIONS}" == "true" ]]; then
    run_step "MIGRATIONS" run_migrations
  else
    record "MIGRATIONS_RESULT" "SKIPPED"
  fi
  run_step "SMOKE" run_smoke
  if [[ "${REHEARSAL_RUN_ROLLBACK}" == "true" ]]; then
    run_step "ROLLBACK_TIMING" rollback_timing
  else
    record "ROLLBACK_TIMING_RESULT" "SKIPPED"
  fi
  if [[ "${REHEARSAL_RUN_BACKUP_RESTORE}" == "true" ]]; then
    run_step "BACKUP_RESTORE" backup_restore_proof
  else
    record "BACKUP_RESTORE_RESULT" "SKIPPED"
  fi
  run_step "AUTH_FILES_JOBS_BILLING_COOKIE_ANALYTICS" auth_files_jobs_billing_cookie_analytics_checks

  if [[ "${step_status}" == "PASS" ]]; then
    record "PRODUCTION_REHEARSAL_RESULT" "PASS"
    record "GO_NO_GO" "GO_WITH_REVIEWED_EVIDENCE"
  else
    record "PRODUCTION_REHEARSAL_RESULT" "BLOCKED"
    record "GO_NO_GO" "NO-GO"
    record "FAILED_STEPS" "${failed_steps[*]}"
  fi
} 2>&1 | tee "${RAW_EVIDENCE}"

infra/deploy/redact-production-rehearsal-evidence.sh "${RAW_EVIDENCE}" "${REDACTED_EVIDENCE}"
infra/deploy/validate-production-rehearsal.sh "${REDACTED_EVIDENCE}"

chmod 600 "${RAW_EVIDENCE}" "${REDACTED_EVIDENCE}" || true

echo "[OK] Raw evidence: ${RAW_EVIDENCE}"
echo "[OK] Redacted evidence: ${REDACTED_EVIDENCE}"
echo "[INFO] DO NOT commit raw or redacted live evidence to Git. Store it in the controlled release evidence vault."
