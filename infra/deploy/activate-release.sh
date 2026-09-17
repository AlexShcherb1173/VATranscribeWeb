#!/usr/bin/env bash
set -Eeuo pipefail
umask 027

FORENSIC_ARTIFACT_ROOT="${FORENSIC_ARTIFACT_ROOT:-/opt/vatranscribe/release-evidence}"
FORENSIC_CAPTURE_DEADLINE_SECONDS=15
FORENSIC_CAPTURE_KILL_GRACE_SECONDS=1
FORENSIC_ARTIFACT_MAX_BYTES=1048576
FORENSIC_ARTIFACT_MAX_COUNT=20
FORENSIC_TOTAL_MAX_BYTES=20971520
FORENSIC_API_WEB_LOG_LINES=300
FORENSIC_API_WEB_LOG_BYTES=262144
FORENSIC_WORKER_LOG_LINES=100
FORENSIC_WORKER_LOG_BYTES=65536

forensic_fixed_warning() {
  printf '%s\n' '[WARN] Release failure evidence diagnostic_collector_result=failure; rollback continues.' >&2
}

forensic_safe_value() {
  # Manifest values are deliberately restricted. Never copy arbitrary command
  # output, log text, health output, or Docker errors through this function.
  printf '%s' "$1" | tr -cd 'A-Za-z0-9_.,:/@+;=|-'
}

forensic_append() {
  local output_file="$1"
  local key="$2"
  local value="$3"
  printf '%s=%s\n' "$key" "$(forensic_safe_value "$value")" >>"${output_file}"
}

forensic_now() {
  date -u +'%Y-%m-%dT%H:%M:%SZ'
}

forensic_container_id() {
  local project_name="$1"
  local service_name="$2"
  local ids
  ids="$(docker ps -a \
    --filter "label=com.docker.compose.project=${project_name}" \
    --filter "label=com.docker.compose.service=${service_name}" \
    --format '{{.ID}}' 2>/dev/null || true)"
  if [[ "$(printf '%s\n' "${ids}" | sed '/^$/d' | wc -l)" -eq 1 ]]; then
    printf '%s' "${ids}"
  fi
}

forensic_selected_state() {
  local output_file="$1"
  local service_name="$2"
  local container_id="$3"
  local state health network ports
  local image_id created status running restarting exit_code oom_killed restart_count started_at finished_at

  if [[ -z "${container_id}" ]]; then
    forensic_append "${output_file}" "${service_name}.container" unavailable
    return 0
  fi

  forensic_append "${output_file}" "${service_name}.container_id" "${container_id}"
  state="$(docker inspect --format \
    '{{.Image}}|{{.Created}}|{{.State.Status}}|{{.State.Running}}|{{.State.Restarting}}|{{.State.ExitCode}}|{{.State.OOMKilled}}|{{.RestartCount}}|{{.State.StartedAt}}|{{.State.FinishedAt}}' \
    "${container_id}" 2>/dev/null || true)"
  if [[ -n "${state}" ]]; then
    IFS='|' read -r image_id created status running restarting exit_code oom_killed restart_count started_at finished_at <<<"${state}"
    forensic_append "${output_file}" "${service_name}.image_id" "${image_id}"
    forensic_append "${output_file}" "${service_name}.created" "${created}"
    forensic_append "${output_file}" "${service_name}.status" "${status}"
    forensic_append "${output_file}" "${service_name}.running" "${running}"
    forensic_append "${output_file}" "${service_name}.restarting" "${restarting}"
    forensic_append "${output_file}" "${service_name}.exit_code" "${exit_code}"
    forensic_append "${output_file}" "${service_name}.oom_killed" "${oom_killed}"
    forensic_append "${output_file}" "${service_name}.restart_count" "${restart_count}"
    forensic_append "${output_file}" "${service_name}.started_at" "${started_at}"
    forensic_append "${output_file}" "${service_name}.finished_at" "${finished_at}"
  else
    forensic_append "${output_file}" "${service_name}.selected_state" unavailable
  fi

  health="$(docker inspect --format \
    '{{if .State.Health}}{{.State.Health.Status}}|{{.State.Health.FailingStreak}}{{range .State.Health.Log}}|{{.Start}},{{.End}},{{.ExitCode}}{{end}}{{else}}unavailable{{end}}' \
    "${container_id}" 2>/dev/null | awk -F'|' '{ printf "%s|%s", $1, $2; start=(NF>7?NF-4:3); for(i=start;i<=NF;i++) if(i>=3) printf "|%s", $i; printf "\n" }' || true)"
  forensic_append "${output_file}" "${service_name}.health_latest_five" "${health:-unavailable}"

  network="$(docker inspect --format \
    '{{range $name,$settings := .NetworkSettings.Networks}}{{$name}},{{$settings.NetworkID}},{{$settings.IPAddress}},{{range $settings.Aliases}}{{.}};{{end}}|{{end}}' \
    "${container_id}" 2>/dev/null || true)"
  forensic_append "${output_file}" "${service_name}.selected_network" "${network:-unavailable}"

  ports="$(docker inspect --format \
    '{{with index .NetworkSettings.Ports "80/tcp"}}80/tcp={{range .}}{{.HostIp}}:{{.HostPort}};{{end}}{{end}}|{{with index .NetworkSettings.Ports "443/tcp"}}443/tcp={{range .}}{{.HostIp}}:{{.HostPort}};{{end}}{{end}}|{{with index .NetworkSettings.Ports "8000/tcp"}}8000/tcp={{range .}}{{.HostIp}}:{{.HostPort}};{{end}}{{end}}' \
    "${container_id}" 2>/dev/null || true)"
  forensic_append "${output_file}" "${service_name}.relevant_ports" "${ports:-none}"
}

forensic_normalize_logs() {
  local output_file="$1"
  local service_name="$2"
  local container_id="$3"
  local max_lines="$4"
  local max_bytes="$5"
  local log_class="$6"

  if [[ -z "${container_id}" ]]; then
    forensic_append "${output_file}" "${service_name}.logs" unavailable
    return 0
  fi

  # Raw logs exist only in this bounded pipe. They are never written to disk,
  # echoed, or included in command errors. awk emits fixed normalized records.
  docker logs --since 10m --timestamps --tail "$((max_lines + 1))" "${container_id}" 2>/dev/null |
    head -c "$((max_bytes + 1))" |
    awk -v service="${service_name}" -v kind="${log_class}" \
      -v max_lines="${max_lines}" -v max_bytes="${max_bytes}" '
      BEGIN { seen=0; recognized=0; omitted=0; bytes=0; truncated="false" }
      {
        seen++; bytes += length($0) + 1
        if (seen > max_lines || bytes > max_bytes) { truncated="true"; omitted++; next }
        ts=$1
        if (ts !~ /^[0-9][0-9][0-9][0-9]-[0-9T:.+-]+Z?$/) ts="unknown"
        category=""; status=""; errnum=""; target=""; port=""
        lower=tolower($0)
        if (match($0, /(^|[^0-9])[1-5][0-9][0-9]([^0-9]|$)/)) {
          candidate=substr($0, RSTART, RLENGTH)
          gsub(/[^0-9]/, "", candidate)
          status=candidate
        }
        if (match(lower, /errno[^0-9]*[0-9]+/)) {
          candidate=substr(lower, RSTART, RLENGTH)
          gsub(/[^0-9]/, "", candidate)
          errnum=candidate
        }
        if (kind == "proxy") {
          if (lower ~ /connection refused/) category="connection_refused"
          else if (lower ~ /host not found|name or service not known|temporary failure in name resolution/) category="name_resolution_failed"
          else if (lower ~ /timed out|timeout/) category="timeout"
          else if (lower ~ /connection reset/) category="connection_reset"
          else if (lower ~ /prematurely closed/) category="premature_close"
          else if (lower ~ /ssl.*handshake|tls.*handshake/) category="TLS_handshake_failure"
          if (match($0, /api:8000/)) { target="api"; port="8000" }
          if (category == "" && lower ~ /\/api\/v1\/health\/(live|ready)/ && status != "") category="proxy_health_http_status"
        } else {
          if (lower ~ /application startup complete/) category="startup"
          else if (lower ~ /uvicorn running on/) category="listening"
          else if (lower ~ /application shutdown complete|shutting down/) category="shutdown"
          else if (lower ~ /permissionerror/) category="PermissionError"
          else if (lower ~ /connectionerror/) category="ConnectionError"
          else if (lower ~ /timeouterror/) category="TimeoutError"
          else if (lower ~ /runtimeerror/) category="RuntimeError"
          else if (lower ~ /valueerror/) category="ValueError"
          if (category == "" && lower ~ /\/api\/v1\/health\/(live|ready)/ && status != "") category="health_http_status"
        }
        if (category != "") {
          printf "%s.log_event.%d=%s,%s", service, recognized+1, ts, category
          if (status != "") printf ",http_status:%s", status
          if (errnum != "") printf ",errno:%s", errnum
          if (target != "") printf ",target:%s,port:%s", target, port
          printf "\n"; recognized++
        } else omitted++
      }
      END {
        printf "%s.log_recognized_count=%d\n", service, recognized
        printf "%s.unrecognized_line_count=%d\n", service, omitted
        printf "%s.omitted_line_count=%d\n", service, omitted
        printf "%s.truncated=%s\n", service, truncated
      }' >>"${output_file}" || forensic_append "${output_file}" "${service_name}.logs" unavailable
}

forensic_probe() {
  local output_file="$1"
  local key="$2"
  shift 2
  local started ended started_ms ended_ms result
  started="$(forensic_now)"
  started_ms="$(date -u +%s%3N 2>/dev/null || date -u +%s000)"
  if "$@" >/dev/null 2>/dev/null; then result=success; else result=unavailable; fi
  ended="$(forensic_now)"
  ended_ms="$(date -u +%s%3N 2>/dev/null || date -u +%s000)"
  forensic_append "${output_file}" "operation.${key}.start" "${started}"
  forensic_append "${output_file}" "operation.${key}.end" "${ended}"
  forensic_append "${output_file}" "operation.${key}.duration_ms" "$((ended_ms - started_ms))"
  forensic_append "${output_file}" "operation.${key}.result" "${result}"
}

forensic_unavailable_operation() {
  local output_file="$1"
  local key="$2"
  local observed_at
  observed_at="$(forensic_now)"
  forensic_append "${output_file}" "operation.${key}.start" "${observed_at}"
  forensic_append "${output_file}" "operation.${key}.end" "${observed_at}"
  forensic_append "${output_file}" "operation.${key}.duration_ms" 0
  forensic_append "${output_file}" "operation.${key}.result" unavailable
}

forensic_network_probe() {
  local output_file="$1"
  local key="$2"
  shift 2
  local started ended started_ms ended_ms raw_output command_status result
  started="$(forensic_now)"
  started_ms="$(date -u +%s%3N 2>/dev/null || date -u +%s000)"
  set +e
  raw_output="$("$@" 2>&1 >/dev/null)"
  command_status=$?
  set -e
  if [[ "${command_status}" -eq 0 ]]; then
    result=success
  elif [[ "${raw_output,,}" =~ connection.refused ]]; then
    result=connection_refused
  elif [[ "${raw_output,,}" =~ (bad.address|host.not.found|name.or.service.not.known|name.resolution) ]]; then
    result=name_resolution_failed
  elif [[ "${raw_output,,}" =~ (timed.out|timeout) ]]; then
    result=timeout
  elif [[ "${raw_output,,}" =~ connection.reset ]]; then
    result=connection_reset
  else
    result=other_known_category
  fi
  # raw_output is intentionally discarded without ever being printed or stored.
  raw_output=''
  ended="$(forensic_now)"
  ended_ms="$(date -u +%s%3N 2>/dev/null || date -u +%s000)"
  forensic_append "${output_file}" "operation.${key}.start" "${started}"
  forensic_append "${output_file}" "operation.${key}.end" "${ended}"
  forensic_append "${output_file}" "operation.${key}.duration_ms" "$((ended_ms - started_ms))"
  forensic_append "${output_file}" "operation.${key}.result" "${result}"
}

capture_failure_evidence() {
  local release_id="$1"
  local original_status="$2"
  local archive_sha="$3"
  local project_name="$4"
  local smoke_base_url="$5"
  local root="${FORENSIC_ARTIFACT_ROOT}"
  local artifact suffix manifest existing_count existing_bytes
  local api_id web_id worker_id worker_state
  local root_mode
  umask 077
  trap 'if [[ -n "${manifest:-}" && -f "${manifest}" && ! -L "${manifest}" ]]; then forensic_append "${manifest}" timeout_status true || true; forensic_append "${manifest}" diagnostic_collector_result timeout || true; forensic_append "${manifest}" capture_complete false || true; fi; exit 124' TERM

  [[ "${release_id}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$ ]] || return 69

  if [[ ! -e "${root}" ]]; then
    mkdir -m 700 -- "${root}" 2>/dev/null || return 70
  fi
  [[ -d "${root}" && ! -L "${root}" && -O "${root}" && -w "${root}" ]] || return 71
  root_mode="$(stat -c '%a' "${root}" 2>/dev/null || true)"
  [[ "${root_mode}" =~ ^[0-7]{3,4}$ ]] || return 71
  (( (8#${root_mode} & 0022) == 0 )) || return 71

  existing_count="$(find "${root}" -mindepth 1 -maxdepth 1 -type d -name 'activation-failure.*' -printf '.' 2>/dev/null | wc -c)"
  existing_bytes="$(find "${root}" -mindepth 1 -maxdepth 1 -type d -name 'activation-failure.*' -exec du -sb {} + 2>/dev/null | awk '{ total += $1 } END { print total + 0 }')"
  if (( existing_count >= FORENSIC_ARTIFACT_MAX_COUNT ||
        existing_bytes + FORENSIC_ARTIFACT_MAX_BYTES > FORENSIC_TOTAL_MAX_BYTES )); then
    printf '%s\n' '[WARN] Release failure evidence capture skipped: capacity.' >&2
    return 72
  fi

  suffix="$(date -u +'%Y%m%dT%H%M%SZ').$$"
  artifact="${root}/activation-failure.${release_id}.${suffix}"
  mkdir -m 700 -- "${artifact}" 2>/dev/null || return 73
  manifest="${artifact}/manifest.txt"
  (umask 077; : >"${manifest}") || return 74
  chmod 600 "${manifest}" 2>/dev/null || return 75

  forensic_append "${manifest}" format_version 1
  forensic_append "${manifest}" release_id "${release_id}"
  forensic_append "${manifest}" archive_sha256 "${archive_sha}"
  forensic_append "${manifest}" original_activation_exit_status "${original_status}"
  forensic_append "${manifest}" capture_start "$(forensic_now)"
  forensic_append "${manifest}" capacity_status available
  forensic_append "${manifest}" capture_complete false
  forensic_append "${manifest}" timeout_status false

  # Freeze label-selected IDs once. All following observations use these IDs.
  forensic_append "${manifest}" operation.container_identity.start "$(forensic_now)"
  api_id="$(forensic_container_id "${project_name}" api)"
  web_id="$(forensic_container_id "${project_name}" web)"
  worker_id="$(forensic_container_id "${project_name}" worker)"
  forensic_append "${manifest}" container_identity_attribution unverified_candidate_observation
  forensic_append "${manifest}" operation.container_identity.end "$(forensic_now)"
  forensic_append "${manifest}" operation.container_identity.result success

  forensic_append "${manifest}" operation.selected_state.start "$(forensic_now)"
  forensic_selected_state "${manifest}" api "${api_id}"
  forensic_selected_state "${manifest}" web "${web_id}"
  forensic_selected_state "${manifest}" worker "${worker_id}"
  forensic_append "${manifest}" operation.selected_state.end "$(forensic_now)"
  forensic_append "${manifest}" operation.selected_state.result success

  forensic_append "${manifest}" operation.normalized_logs.start "$(forensic_now)"
  forensic_normalize_logs "${manifest}" api "${api_id}" \
    "${FORENSIC_API_WEB_LOG_LINES}" "${FORENSIC_API_WEB_LOG_BYTES}" api
  forensic_normalize_logs "${manifest}" web "${web_id}" \
    "${FORENSIC_API_WEB_LOG_LINES}" "${FORENSIC_API_WEB_LOG_BYTES}" proxy

  worker_state="$(docker inspect --format '{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}unavailable{{end}}' "${worker_id}" 2>/dev/null || true)"
  if [[ -z "${worker_id}" ]]; then
    forensic_append "${manifest}" worker.logs unavailable
  elif [[ "${worker_state}" =~ (exited|restarting|unhealthy|dead) ]]; then
    forensic_normalize_logs "${manifest}" worker "${worker_id}" \
      "${FORENSIC_WORKER_LOG_LINES}" "${FORENSIC_WORKER_LOG_BYTES}" api
  else
    forensic_append "${manifest}" worker.logs not_required
  fi
  forensic_append "${manifest}" operation.normalized_logs.end "$(forensic_now)"
  forensic_append "${manifest}" operation.normalized_logs.result success

  if [[ -n "${api_id}" ]]; then
    forensic_probe "${manifest}" api_live docker exec --user 10001:10001 "${api_id}" \
      python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=3).read(0)"
    forensic_probe "${manifest}" api_ready docker exec --user 10001:10001 "${api_id}" \
      python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/ready', timeout=3).read(0)"
    forensic_probe "${manifest}" api_listening docker exec "${api_id}" sh -c \
      "awk 'NR > 1 && \$2 ~ /:1F40$/ && \$4 == \"0A\" { found=1 } END { exit !found }' /proc/net/tcp /proc/net/tcp6"
  else
    forensic_unavailable_operation "${manifest}" api_live
    forensic_unavailable_operation "${manifest}" api_ready
    forensic_unavailable_operation "${manifest}" api_listening
  fi

  if [[ -n "${web_id}" ]]; then
    forensic_probe "${manifest}" web_health docker exec "${web_id}" wget -q -T 3 -O /dev/null http://127.0.0.1/healthz
    forensic_network_probe "${manifest}" web_to_api docker exec "${web_id}" wget -q -T 3 -O /dev/null http://api:8000/api/v1/health/live
    forensic_unavailable_operation "${manifest}" web_https_live
  else
    forensic_unavailable_operation "${manifest}" web_health
    forensic_unavailable_operation "${manifest}" web_to_api
    forensic_unavailable_operation "${manifest}" web_https_live
  fi

  if command -v curl >/dev/null 2>&1; then
    forensic_probe "${manifest}" public_live curl --fail --silent --show-error --max-time 3 \
      --output /dev/null "${smoke_base_url%/}/api/v1/health/live"
  else
    forensic_unavailable_operation "${manifest}" public_live
  fi

  forensic_append "${manifest}" capture_end "$(forensic_now)"
  if (( $(du -sb "${artifact}" 2>/dev/null | awk '{print $1 + 0}') > FORENSIC_ARTIFACT_MAX_BYTES )); then
    forensic_append "${manifest}" artifact_size_status exceeded
    forensic_append "${manifest}" diagnostic_collector_result artifact_limit_exceeded
    return 76
  fi
  forensic_append "${manifest}" diagnostic_collector_result success
  forensic_append "${manifest}" capture_complete true
  trap - TERM
}

if [[ "${1:-}" == "--capture-failure-evidence" ]]; then
  shift
  capture_failure_evidence "$@"
  exit $?
fi

RELEASE_ARCHIVE="${1:-${RELEASE_ARCHIVE:-}}"
RELEASE_CHECKSUM="${2:-${RELEASE_CHECKSUM:-}}"
PROJECT_ROOT="${PROJECT_ROOT:-/opt/vatranscribe/app}"
PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
CERTBOT_ROOT="${CERTBOT_ROOT:-/opt/vatranscribe/certbot}"
SMOKE_BASE_URL="${SMOKE_BASE_URL:-https://api.vatranscribe.ru}"
COMPOSE_FILES="${COMPOSE_FILES:-docker-compose.yml -f infra/compose/docker-compose.prod.yml}"
LOCK_FILE="${LOCK_FILE:-/tmp/vatranscribe-release-activation.lock}"
RELEASE_RETENTION_COUNT="${RELEASE_RETENTION_COUNT:-3}"

[[ -n "${RELEASE_ARCHIVE}" ]] || { echo "Release archive is required." >&2; exit 64; }
[[ -n "${RELEASE_CHECKSUM}" ]] || { echo "Release checksum is required." >&2; exit 64; }
[[ -f "${RELEASE_ARCHIVE}" ]] || { echo "Release archive not found." >&2; exit 66; }
[[ -f "${RELEASE_CHECKSUM}" ]] || { echo "Release checksum not found." >&2; exit 66; }
[[ -d "${PROJECT_ROOT}" ]] || { echo "Project root not found." >&2; exit 66; }
[[ -f "${RUNTIME_ENV_FILE}" ]] || { echo "Runtime env file not found." >&2; exit 66; }
[[ -d "${CERTBOT_ROOT}" ]] || { echo "Certbot runtime root not found." >&2; exit 66; }

PROJECT_ROOT="$(realpath -m "${PROJECT_ROOT}")"
RUNTIME_ENV_FILE="$(realpath -m "${RUNTIME_ENV_FILE}")"
CERTBOT_ROOT="$(realpath -m "${CERTBOT_ROOT}")"
PROJECT_PARENT="$(dirname "${PROJECT_ROOT}")"

[[ "$(basename "${PROJECT_ROOT}")" == "app" ]] || {
  echo "Project root must end with /app." >&2
  exit 65
}

[[ "$(dirname "${CERTBOT_ROOT}")" == "${PROJECT_PARENT}" ]] || {
  echo "Certbot root must be a sibling of the project root." >&2
  exit 65
}

[[ "$(basename "${CERTBOT_ROOT}")" == "certbot" ]] || {
  echo "Unexpected Certbot root name." >&2
  exit 65
}

[[ -d "${PROJECT_PARENT}" && -w "${PROJECT_PARENT}" ]] || {
  echo "Project parent is not writable." >&2
  exit 73
}

RELEASE_ID="${RELEASE_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}"

[[ "${RELEASE_ID}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$ ]] || {
  echo "Release ID contains unsupported characters." >&2
  exit 65
}

[[ "${RELEASE_RETENTION_COUNT}" =~ ^[0-9]+$ ]] || {
  echo "RELEASE_RETENTION_COUNT must be an integer." >&2
  exit 65
}

if (( RELEASE_RETENTION_COUNT < 1 || RELEASE_RETENTION_COUNT > 20 )); then
  echo "RELEASE_RETENTION_COUNT must be between 1 and 20." >&2
  exit 65
fi

STAGING_ROOT="${PROJECT_PARENT}/app.next.${RELEASE_ID}"
PREVIOUS_ROOT="${PROJECT_PARENT}/app.prev.${RELEASE_ID}"
BROKEN_ROOT="${PROJECT_PARENT}/app.broken.${RELEASE_ID}"
ROTATED="false"
RELEASE_COMMITTED="false"

compose_from_root() {
  local root="$1"
  shift
  (
    cd "${root}"
    # shellcheck disable=SC2086
    docker compose --env-file "${RUNTIME_ENV_FILE}" -p "${PROJECT_NAME}" -f ${COMPOSE_FILES} "$@"
  )
}

inspect_release_mounts() {
  local path child inventory status index=0
  local -a pending=("$1")
  inventory="$(mktemp)" || return $?
  while (( index < ${#pending[@]} )); do
    path="${pending[index]}"
    index=$((index + 1))
    # Never probe through a symlink. Enumerate only immediate children after
    # their parent is authoritatively known not to be a mount boundary.
    [[ ! -L "${path}" ]] || continue
    if mountpoint -q -- "${path}"; then
      status=0
    else
      status=$?
    fi
    case "${status}" in
      0)
        printf '[ERROR] POST_COMMIT_PRUNE_FAILED category=mounted_state path=%q\n' "${path}" >&2
        rm -f -- "${inventory}"
        return 73;;
      32) :;; # util-linux: authoritative non-mountpoint
      *)
        printf '[ERROR] POST_COMMIT_PRUNE_FAILED category=MOUNT_PROBE_ERROR path=%q probe_status=%s\n' "${path}" "${status}" >&2
        rm -f -- "${inventory}"
        return "${status}";;
    esac
    if [[ -d "${path}" ]]; then
      if find -P "${path}" -mindepth 1 -maxdepth 1 ! -type l -print0 >"${inventory}"; then
        while IFS= read -r -d '' child; do
          pending+=("${child}")
        done <"${inventory}"
      else
        status=$?
        printf '[ERROR] POST_COMMIT_PRUNE_FAILED category=inspection_failed path=%q exit_status=%s\n' "${path}" "${status}" >&2
        rm -f -- "${inventory}"
        return "${status}"
      fi
    fi
  done
  rm -f -- "${inventory}"
}

prune_release_directories() {
  local pattern="$1"
  local keep_count="$2"
  local entry directory basename_value inventory status
  local seen=0

  # Failed candidates and release-evidence are forensic records, not cleanup
  # targets. Legacy real Certbot directories also require separate review.
  [[ "${pattern}" == 'app.prev.*' ]] || return 65
  inventory="$(mktemp)" || return $?
  if find "${PROJECT_PARENT}" -mindepth 1 -maxdepth 1 -type d \
    -name "${pattern}" -printf '%T@ %p\0' | sort -z -nr >"${inventory}"; then
    :
  else
    status=$?
    printf '[ERROR] POST_COMMIT_PRUNE_FAILED category=enumeration path=%q exit_status=%s\n' "${PROJECT_PARENT}" "${status}" >&2
    rm -f -- "${inventory}"
    return "${status}"
  fi

  while IFS= read -r -d '' entry; do
    directory="${entry#* }"
    seen=$((seen + 1))

    if (( seen <= keep_count )); then
      continue
    fi

    basename_value="$(basename "${directory}")"
    if [[ "$(dirname "${directory}")" != "${PROJECT_PARENT}" ||
          ! "${basename_value}" =~ ^app\.prev\.[A-Za-z0-9][A-Za-z0-9._-]*$ ||
          -L "${directory}" || ! -d "${directory}" ||
          "$(realpath -e -- "${directory}")" != "${directory}" ]]; then
      printf '[ERROR] POST_COMMIT_PRUNE_FAILED category=unsafe_path path=%q\n' "${directory}" >&2
      rm -f -- "${inventory}"
      return 65
    fi
    # Never traverse a legacy release's real mutable certificate tree. Symlinks
    # are unlinked by rm, never followed (including nested/outside symlinks).
    if [[ ! -L "${directory}/infra" && -d "${directory}/infra/certbot" &&
          ! -L "${directory}/infra/certbot" ]]; then
      printf '[ERROR] POST_COMMIT_PRUNE_FAILED category=legacy_certbot_state path=%q\n' "${directory}/infra/certbot" >&2
      rm -f -- "${inventory}"
      return 73
    fi
    # Device boundaries alone do not catch bind mounts on the same filesystem.
    # Inspect without following symlinks; stop at a mount instead of descending.
    if inspect_release_mounts "${directory}"; then
      :
    else
      status=$?
      rm -f -- "${inventory}"
      return "${status}"
    fi
    if rm -rf --one-file-system --preserve-root=all -- "${directory}"; then
      printf '[INFO] POST_COMMIT_PRUNE_REMOVED path=%q\n' "${directory}"
    else
      status=$?
      printf '[ERROR] POST_COMMIT_PRUNE_FAILED category=remove_failed path=%q exit_status=%s\n' "${directory}" "${status}" >&2
      rm -f -- "${inventory}"
      return "${status}"
    fi
  done <"${inventory}"
  rm -f -- "${inventory}"
}

restore_previous_release() {
  if [[ "${ROTATED}" != "true" || "${RELEASE_COMMITTED}" == "true" ]]; then
    return 0
  fi

  set +e
  echo "Release activation failed; restoring previous release." >&2

  if [[ -d "${PROJECT_ROOT}" ]]; then
    mv "${PROJECT_ROOT}" "${BROKEN_ROOT}"
  fi

  if [[ -d "${PREVIOUS_ROOT}" ]]; then
    mv "${PREVIOUS_ROOT}" "${PROJECT_ROOT}"
  fi

  if [[ -d "${PROJECT_ROOT}" ]]; then
    ln -sfn "${RUNTIME_ENV_FILE}" "${PROJECT_ROOT}/.env"
    rm -rf "${PROJECT_ROOT}/infra/certbot"
    ln -sfn "${CERTBOT_ROOT}" "${PROJECT_ROOT}/infra/certbot"
    compose_from_root "${PROJECT_ROOT}" build
    compose_from_root "${PROJECT_ROOT}" up -d db redis
    compose_from_root "${PROJECT_ROOT}" up -d --remove-orphans --force-recreate --no-deps api worker web
  fi

  ROTATED="false"
  set -e
}

cleanup() {
  local status=$?
  local diagnostic_status=0
  trap - EXIT

  if [[ "${status}" -ne 0 ]]; then
    if [[ "${RELEASE_COMMITTED}" == "true" ]]; then
      printf '[ERROR] RELEASE_POST_COMMIT_FAILURE release_id=%s exit_status=%s candidate_active=true rollback_performed=false\n' "${RELEASE_ID}" "${status}" >&2
    elif [[ "${ROTATED}" == "true" ]]; then
      if command -v timeout >/dev/null 2>&1 && command -v setsid >/dev/null 2>&1; then
        set +e
        setsid sh -c '
          timeout --signal=TERM --kill-after="$1" "$2" \
            bash "$3" --capture-failure-evidence \
              "$4" "$5" "$6" "$7" "$8"
        ' forensic-capture \
          "${FORENSIC_CAPTURE_KILL_GRACE_SECONDS}s" \
          "${FORENSIC_CAPTURE_DEADLINE_SECONDS}s" \
          "$0" "${RELEASE_ID}" "${status}" "${actual_sha:-unavailable}" \
          "${PROJECT_NAME}" "${SMOKE_BASE_URL}" 9>&- >/dev/null 2>&1
        diagnostic_status=$?
        set -e
        if [[ "${diagnostic_status}" -ne 0 ]]; then
          case "${diagnostic_status}" in
            72) printf '%s\n' '[WARN] Release failure evidence capture_skipped=capacity; rollback continues.' >&2 ;;
            124|137) printf '%s\n' '[WARN] Release failure evidence timeout=true; rollback continues.' >&2 ;;
            *) forensic_fixed_warning ;;
          esac
        fi
      else
        forensic_fixed_warning
      fi
      restore_previous_release || true
    fi
  fi

  rm -rf "${STAGING_ROOT}"
  rm -f "${RELEASE_ARCHIVE}" "${RELEASE_CHECKSUM}"

  case "$0" in
    /tmp/vatranscribe-*.activate-release.sh)
      rm -f "$0"
      ;;
  esac
  exit "${status}"
}

trap cleanup EXIT

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo "Another release activation is already running." >&2
  exit 75
fi

checksum_directory="$(dirname "${RELEASE_CHECKSUM}")"
archive_directory="$(dirname "${RELEASE_ARCHIVE}")"

[[ "${checksum_directory}" == "${archive_directory}" ]] || {
  echo "Archive and checksum must be in the same directory." >&2
  exit 65
}

checksum_line_count="$(awk 'NF { count++ } END { print count + 0 }' "${RELEASE_CHECKSUM}")"

[[ "${checksum_line_count}" == "1" ]] || {
  echo "Checksum file must contain exactly one non-empty line." >&2
  exit 65
}

expected_sha="$(awk 'NF { print $1; exit }' "${RELEASE_CHECKSUM}")"

[[ "${expected_sha}" =~ ^[0-9a-fA-F]{64}$ ]] || {
  echo "Checksum file contains an invalid SHA-256 value." >&2
  exit 65
}

actual_sha="$(sha256sum "${RELEASE_ARCHIVE}" | awk '{ print $1 }')"

[[ "${actual_sha,,}" == "${expected_sha,,}" ]] || {
  echo "Release archive SHA-256 mismatch." >&2
  exit 65
}

while IFS= read -r archive_path; do
  [[ -n "${archive_path}" ]] || continue

  case "${archive_path}" in
    /*|..|../*|*/..|*/../*)
      echo "Archive contains unsafe path: ${archive_path}" >&2
      exit 65
      ;;
  esac
done < <(tar -tzf "${RELEASE_ARCHIVE}")

mkdir -p "${STAGING_ROOT}"
chmod 775 "${STAGING_ROOT}"

# Payload validation accepts only Git 100644/100755 files. Preserve those modes
# despite umask 027 while keeping ownership untrusted with --no-same-owner;
# --no-same-permissions here would make files unreadable to non-root runtimes.
tar \
  --extract \
  --gzip \
  --file "${RELEASE_ARCHIVE}" \
  --directory "${STAGING_ROOT}" \
  --no-same-owner \
  --same-permissions \
  --delay-directory-restore

if find "${STAGING_ROOT}" -xdev -type l -print -quit | grep -q .; then
  echo "Release archive contains a symbolic link." >&2
  exit 65
fi

if find "${STAGING_ROOT}" -xdev \
  ! -type f \
  ! -type d \
  -print -quit | grep -q .; then
  echo "Release archive contains an unsupported filesystem entry." >&2
  exit 65
fi

for required in \
  docker-compose.yml \
  infra/compose/docker-compose.prod.yml \
  infra/deploy/deploy.sh \
  infra/deploy/validate-production-secrets.sh \
  infra/backup/backup-postgres.sh; do
  [[ -f "${STAGING_ROOT}/${required}" ]] || {
    echo "Required release file is missing: ${required}" >&2
    exit 66
  }
done

bash "${STAGING_ROOT}/infra/deploy/validate-production-secrets.sh" "${RUNTIME_ENV_FILE}"
ln -sfn "${RUNTIME_ENV_FILE}" "${STAGING_ROOT}/.env"

rm -rf "${STAGING_ROOT}/infra/certbot"
ln -sfn "${CERTBOT_ROOT}" "${STAGING_ROOT}/infra/certbot"

if [[ -d "${PROJECT_ROOT}/infra/deploy/.p3-02-backups" ]]; then
  mkdir -p "${STAGING_ROOT}/infra/deploy"
  cp -a \
    "${PROJECT_ROOT}/infra/deploy/.p3-02-backups" \
    "${STAGING_ROOT}/infra/deploy/"
fi

(
  cd "${PROJECT_ROOT}"
  PROJECT_ROOT="${PROJECT_ROOT}" \
  PROJECT_NAME="${PROJECT_NAME}" \
  RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE}" \
  COMPOSE_FILES="${COMPOSE_FILES}" \
    bash "${STAGING_ROOT}/infra/backup/backup-postgres.sh"
)

[[ ! -e "${PREVIOUS_ROOT}" ]] || { echo "Previous release target already exists." >&2; exit 73; }

mv "${PROJECT_ROOT}" "${PREVIOUS_ROOT}"
ROTATED="true"
mv "${STAGING_ROOT}" "${PROJECT_ROOT}"

PROJECT_ROOT="${PROJECT_ROOT}" \
PROJECT_NAME="${PROJECT_NAME}" \
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE}" \
SMOKE_BASE_URL="${SMOKE_BASE_URL}" \
COMPOSE_FILES="${COMPOSE_FILES}" \
BACKUP_BEFORE_DEPLOY="false" \
  bash "${PROJECT_ROOT}/infra/deploy/deploy.sh"

# deploy.sh returns only after migration, replacement, readiness and both smoke
# checks succeed. No later housekeeping error may undo this accepted release.
RELEASE_COMMITTED="true"
ROTATED="false"
printf '[INFO] RELEASE_COMMIT_POINT release_id=%s candidate_active=true\n' "${RELEASE_ID}"

prune_release_directories "app.prev.*" "${RELEASE_RETENTION_COUNT}"
printf '[INFO] POST_COMMIT_PRUNE_COMPLETE release_id=%s broken_candidates=preserved\n' "${RELEASE_ID}"
echo "Release activation completed: ${PROJECT_ROOT}"
