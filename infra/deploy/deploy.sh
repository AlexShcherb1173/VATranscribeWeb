#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/opt/vatranscribe/app}"
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"
READINESS_POLL_INTERVAL_SECONDS=5
READINESS_TIMEOUT_SECONDS=175

api_readiness_log() {
  local level="$1"
  local category="$2"
  local candidate_id="${3:-unavailable}"
  local lifecycle_status="${4:-unavailable}"
  local health_status="${5:-unavailable}"
  local elapsed_seconds="${6:-0}"

  printf '[%s] API_READINESS category=%s candidate_id=%s lifecycle=%s health=%s elapsed_seconds=%s\n' \
    "${level}" \
    "${category}" \
    "${candidate_id}" \
    "${lifecycle_status}" \
    "${health_status}" \
    "${elapsed_seconds}" >&2
}

wait_for_candidate_api_readiness() {
  local started_at deadline now remaining elapsed sleep_seconds command_status
  local selected_output inspect_output ready_status candidate_id
  local frozen_candidate_id="unavailable"
  local lifecycle_status="unavailable"
  local running_status="unavailable"
  local restarting_status="unavailable"
  local health_status="unavailable"
  local -a candidate_ids=()

  if ! command -v timeout >/dev/null 2>&1; then
    api_readiness_log ERROR API_READINESS_TOOL_UNAVAILABLE
    return 70
  fi

  if ! started_at="$(date -u +%s 2>/dev/null)" || [[ ! "${started_at}" =~ ^[0-9]+$ ]]; then
    api_readiness_log ERROR API_READINESS_TOOL_UNAVAILABLE
    return 70
  fi
  deadline=$((started_at + READINESS_TIMEOUT_SECONDS))

  refresh_readiness_budget() {
    if ! now="$(date -u +%s 2>/dev/null)" || [[ ! "${now}" =~ ^[0-9]+$ ]]; then
      api_readiness_log ERROR API_READINESS_TOOL_UNAVAILABLE \
        "${frozen_candidate_id}" "${lifecycle_status}" "${health_status}" 0
      return 70
    fi
    elapsed=$((now - started_at))
    if (( now >= deadline )); then
      api_readiness_log ERROR API_READINESS_TIMEOUT \
        "${frozen_candidate_id}" "${lifecycle_status}" "${health_status}" "${elapsed}"
      return 124
    fi
    remaining=$((deadline - now))
    return 0
  }

  bounded_candidate_selection() {
    if refresh_readiness_budget; then
      :
    else
      return $?
    fi
    if selected_output="$(
      timeout --signal=TERM --kill-after=2s "${remaining}s" \
        docker ps -aq --no-trunc \
          --filter "label=com.docker.compose.project=${PROJECT_NAME}" \
          --filter 'label=com.docker.compose.service=api' \
          2>/dev/null
    )"; then
      command_status=0
    else
      command_status=$?
    fi
    if (( command_status != 0 )); then
      if refresh_readiness_budget; then
        api_readiness_log ERROR API_READINESS_INSPECT_FAILURE \
          "${frozen_candidate_id}" "${lifecycle_status}" "${health_status}" "${elapsed}"
        return 77
      else
        command_status=$?
        return "${command_status}"
      fi
    fi
    candidate_ids=()
    while IFS= read -r candidate_id; do
      [[ -n "${candidate_id}" ]] && candidate_ids+=("${candidate_id}")
    done <<<"${selected_output}"
    if (( ${#candidate_ids[@]} == 0 )); then
      refresh_readiness_budget || return $?
      api_readiness_log ERROR API_READINESS_IDENTITY_MISSING \
        "${frozen_candidate_id}" "${lifecycle_status}" "${health_status}" "${elapsed}"
      return 71
    fi
    if (( ${#candidate_ids[@]} != 1 )); then
      refresh_readiness_budget || return $?
      api_readiness_log ERROR API_READINESS_IDENTITY_AMBIGUOUS \
        "${frozen_candidate_id}" "${lifecycle_status}" "${health_status}" "${elapsed}"
      return 72
    fi
    return 0
  }

  if bounded_candidate_selection; then
    frozen_candidate_id="${candidate_ids[0]}"
  else
    return $?
  fi
  refresh_readiness_budget || return $?
  api_readiness_log INFO API_READINESS_GATE_START \
    "${frozen_candidate_id}" "unavailable" "unavailable" "${elapsed}"

  while true; do
    if bounded_candidate_selection; then
      :
    else
      return $?
    fi
    if [[ "${candidate_ids[0]}" != "${frozen_candidate_id}" ]]; then
      refresh_readiness_budget || return $?
      api_readiness_log ERROR API_READINESS_IDENTITY_CHANGED \
        "${frozen_candidate_id}" "${lifecycle_status}" "${health_status}" "${elapsed}"
      return 73
    fi

    refresh_readiness_budget || return $?
    if inspect_output="$(
      timeout --signal=TERM --kill-after=2s "${remaining}s" \
        docker inspect \
          --format '{{.State.Status}}|{{.State.Running}}|{{.State.Restarting}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' \
          "${frozen_candidate_id}" \
          2>/dev/null
    )"; then
      command_status=0
    else
      command_status=$?
    fi
    if (( command_status != 0 )); then
      if refresh_readiness_budget; then
        api_readiness_log ERROR API_READINESS_INSPECT_FAILURE \
          "${frozen_candidate_id}" "${lifecycle_status}" "${health_status}" "${elapsed}"
        return 77
      else
        command_status=$?
        return "${command_status}"
      fi
    fi

    IFS='|' read -r lifecycle_status running_status restarting_status health_status <<<"${inspect_output}"
    if [[ -z "${lifecycle_status}" || -z "${running_status}" || -z "${restarting_status}" || -z "${health_status}" ]]; then
      refresh_readiness_budget || return $?
      api_readiness_log ERROR API_READINESS_INSPECT_FAILURE \
        "${frozen_candidate_id}" "${lifecycle_status:-unavailable}" "${health_status:-unavailable}" "${elapsed}"
      return 77
    fi
    if [[ "${running_status}" != "true" || "${restarting_status}" != "false" || "${lifecycle_status}" != "running" ]]; then
      refresh_readiness_budget || return $?
      api_readiness_log ERROR API_READINESS_CONTAINER_TERMINAL \
        "${frozen_candidate_id}" "${lifecycle_status}" "${health_status}" "${elapsed}"
      return 75
    fi

    case "${health_status}" in
      missing)
        refresh_readiness_budget || return $?
        api_readiness_log ERROR API_READINESS_HEALTHCHECK_MISSING \
          "${frozen_candidate_id}" "${lifecycle_status}" "${health_status}" "${elapsed}"
        return 74
        ;;
      unhealthy)
        refresh_readiness_budget || return $?
        api_readiness_log ERROR API_READINESS_UNHEALTHY \
          "${frozen_candidate_id}" "${lifecycle_status}" "${health_status}" "${elapsed}"
        return 76
        ;;
      starting)
        ;;
      healthy)
        refresh_readiness_budget || return $?
        if ready_status="$(
          timeout --signal=TERM --kill-after=2s "${remaining}s" \
            docker exec --user 10001:10001 "${frozen_candidate_id}" \
              python -c 'import sys, urllib.error, urllib.request
try:
    response = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/health/ready", timeout=3)
    status = response.status
    response.close()
except urllib.error.HTTPError as exc:
    status = exc.code
except Exception:
    sys.exit(1)
print(status)' \
            2>/dev/null
        )"; then
          command_status=0
        else
          command_status=$?
        fi
        if (( command_status != 0 )); then
          if refresh_readiness_budget; then
            api_readiness_log ERROR API_READINESS_READY_PROBE_FAILURE \
              "${frozen_candidate_id}" "${lifecycle_status}" "${health_status}" "${elapsed}"
            return 79
          else
            command_status=$?
            return "${command_status}"
          fi
        fi
        case "${ready_status}" in
          200)
            refresh_readiness_budget || return $?
            api_readiness_log INFO API_READINESS_PASS \
              "${frozen_candidate_id}" "${lifecycle_status}" "${health_status}" "${elapsed}"
            return 0
            ;;
          503)
            ;;
          *)
            refresh_readiness_budget || return $?
            api_readiness_log ERROR API_READINESS_READY_UNEXPECTED_STATUS \
              "${frozen_candidate_id}" "${lifecycle_status}" "${health_status}" "${elapsed}"
            return 78
            ;;
        esac
        ;;
      *)
        refresh_readiness_budget || return $?
        api_readiness_log ERROR API_READINESS_INSPECT_FAILURE \
          "${frozen_candidate_id}" "${lifecycle_status}" "${health_status}" "${elapsed}"
        return 77
        ;;
    esac

    refresh_readiness_budget || return $?
    sleep_seconds="${READINESS_POLL_INTERVAL_SECONDS}"
    if (( remaining < sleep_seconds )); then
      sleep_seconds="${remaining}"
    fi
    sleep "${sleep_seconds}"
  done
}

cd "${PROJECT_ROOT}"

bash ./infra/deploy/validate-production-secrets.sh "${RUNTIME_ENV_FILE}"
ln -sfn "${RUNTIME_ENV_FILE}" "${PROJECT_ROOT}/.env"

if [[ "${CHECK_DOMAIN_READINESS:-false}" == "true" ]]; then
  bash ./infra/deploy/check-domain-readiness.sh
fi

if [[ "${BACKUP_BEFORE_DEPLOY}" == "true" ]]; then
  PROJECT_ROOT="${PROJECT_ROOT}" \
  PROJECT_NAME="${PROJECT_NAME}" \
  RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE}" \
  COMPOSE_FILES="${COMPOSE_FILES}" \
    bash ./infra/backup/backup-postgres.sh
fi

# shellcheck disable=SC2086
docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} build

if [[ "${RUN_MIGRATIONS}" == "true" ]]; then
  # shellcheck disable=SC2086
  docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} run --rm api python -m alembic upgrade head
fi

# shellcheck disable=SC2086
# Ensure stateful dependencies exist without forcing recreation.
# shellcheck disable=SC2086
docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} up -d db redis

# Recreate only services that consume the activated application release.
# shellcheck disable=SC2086
docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} up -d --remove-orphans --force-recreate --no-deps api worker web

wait_for_candidate_api_readiness

bash ./infra/deploy/smoke-test.sh
bash ./infra/deploy/monitoring-smoke.sh
