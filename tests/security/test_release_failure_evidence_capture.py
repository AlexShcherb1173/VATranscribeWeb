import os
from pathlib import Path
import re
import shutil
import stat
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
ACTIVATOR = ROOT / "infra/deploy/activate-release.sh"
BACKEND_CI = ROOT / ".github/workflows/backend-ci.yml"


def source() -> str:
    return ACTIVATOR.read_text(encoding="utf-8")


def cleanup_body() -> str:
    text = source()
    return text[text.index("cleanup() {") : text.index("\n}\n\ntrap cleanup EXIT")]


def test_failure_capture_precedes_unchanged_rollback_and_preserves_status():
    body = cleanup_body()
    assert body.index("local status=$?") < body.index("setsid sh -c")
    assert body.index("setsid sh -c") < body.index("restore_previous_release || true")
    assert body.index("restore_previous_release || true") < body.index('exit "${status}"')
    assert '[[ "${ROTATED}" == "true" ]]' in body
    assert "diagnostic_status=$?" in body
    assert 'exit "${diagnostic_status}"' not in body


def test_capture_is_bounded_and_child_closes_activation_lock():
    text = source()
    assert "FORENSIC_CAPTURE_DEADLINE_SECONDS=15" in text
    assert "FORENSIC_CAPTURE_KILL_GRACE_SECONDS=1" in text
    assert "setsid sh -c" in text
    assert "timeout --signal=TERM" in text
    assert 'timeout --signal=TERM --kill-after="$1" "$2"' in text
    assert '"${FORENSIC_CAPTURE_KILL_GRACE_SECONDS}s"' in text
    assert '"${FORENSIC_CAPTURE_DEADLINE_SECONDS}s"' in text
    assert "9>&-" in cleanup_body()
    assert "forensic_fixed_warning" in cleanup_body()


def test_success_and_pre_rotation_paths_do_not_capture():
    body = cleanup_body()
    outer = body.index('if [[ "${status}" -ne 0 ]]')
    rotated = body.index('if [[ "${ROTATED}" == "true" ]]')
    capture = body.index("setsid sh -c")
    rollback = body.index("restore_previous_release || true")
    assert outer < rotated < capture < rollback


def test_container_ids_are_label_selected_and_frozen_once():
    text = source()
    assert "label=com.docker.compose.project=${project_name}" in text
    assert "label=com.docker.compose.service=${service_name}" in text
    for service in ("api", "web", "worker"):
        assignment = f'{service}_id="$(forensic_container_id "${{project_name}}" {service})"'
        assert text.count(assignment) == 1
        assert f'forensic_selected_state "${{manifest}}" {service} "${{{service}_id}}"' in text
    assert "unverified_candidate_observation" in text


def test_selected_inspection_excludes_sensitive_docker_fields():
    text = source()
    assert ".Config.Env" not in text
    assert "{{json .State}}" not in text
    assert "docker compose config" not in text
    assert "docker inspect" in text
    assert "{{.State.Health.Status}}" in text
    assert "{{.State.Health.FailingStreak}}" in text
    assert "{{range .State.Health.Log}}" in text
    assert "{{.Output}}" not in text
    for field in (
        "image_id",
        "created",
        "status",
        "running",
        "restarting",
        "exit_code",
        "oom_killed",
        "restart_count",
        "started_at",
        "finished_at",
    ):
        assert f'"${{service_name}}.{field}"' in text


def test_log_limits_and_normalization_are_explicit():
    text = source()
    assert "FORENSIC_API_WEB_LOG_LINES=300" in text
    assert "FORENSIC_API_WEB_LOG_BYTES=262144" in text
    assert "FORENSIC_WORKER_LOG_LINES=100" in text
    assert "FORENSIC_WORKER_LOG_BYTES=65536" in text
    assert "docker logs --since 10m --timestamps" in text
    assert "unrecognized_line_count" in text
    assert "omitted_line_count" in text
    assert "truncated=" in text
    assert "connection_refused" in text
    assert "name_resolution_failed" in text
    assert "premature_close" in text
    assert "TLS_handshake_failure" in text
    assert "health_http_status" in text
    assert '",errno:%s"' in text
    assert "forensic_network_probe" in text


def test_artifact_capacity_collision_and_permissions_contract():
    text = source()
    assert "FORENSIC_ARTIFACT_MAX_BYTES=1048576" in text
    assert "FORENSIC_ARTIFACT_MAX_COUNT=20" in text
    assert "FORENSIC_TOTAL_MAX_BYTES=20971520" in text
    assert "activation-failure.${release_id}.${suffix}" in text
    assert "mkdir -m 700" in text
    assert 'chmod 600 "${manifest}"' in text
    assert "capture skipped: capacity" in text
    assert "rm -rf" not in text[text.index("capture_failure_evidence() {") : text.index('if [[ "${1:-}"')]
    assert '[[ -d "${root}" && ! -L "${root}" && -O "${root}" && -w "${root}" ]]' in text


def test_manifest_has_required_normalized_metadata():
    text = source()
    for key in (
        "release_id",
        "archive_sha256",
        "original_activation_exit_status",
        "capture_start",
        "capture_end",
        "capacity_status",
        "capture_complete",
        "timeout_status",
        "diagnostic_collector_result",
    ):
        assert re.search(rf'forensic_append "\$\{{manifest\}}" {key}\b', text)
    assert "forensic_unavailable_operation" in text


def test_backend_ci_routes_forensic_test_in_existing_linux_job():
    workflow = BACKEND_CI.read_text(encoding="utf-8")
    assert "name: Backend CI" in workflow
    assert "pull_request:" in workflow
    assert "docker-api-build:" in workflow
    assert "runs-on: ubuntu-latest" in workflow
    assert "Validate deployment filesystem regressions" in workflow
    assert workflow.count("tests/security/test_release_failure_evidence_capture.py") == 1


def test_backup_filemode_and_success_commands_remain_present():
    text = source()
    assert 'bash "${STAGING_ROOT}/infra/backup/backup-postgres.sh"' in text
    assert "--same-permissions" in text
    assert "--no-same-owner" in text
    assert 'bash "${PROJECT_ROOT}/infra/deploy/deploy.sh"' in text
    rollback = text[text.index("restore_previous_release() {") : text.index("cleanup() {")]
    expected = [
        'mv "${PROJECT_ROOT}" "${BROKEN_ROOT}"',
        'mv "${PREVIOUS_ROOT}" "${PROJECT_ROOT}"',
        'compose_from_root "${PROJECT_ROOT}" build',
        'compose_from_root "${PROJECT_ROOT}" up -d db redis',
        'compose_from_root "${PROJECT_ROOT}" up -d --remove-orphans --force-recreate --no-deps api worker web',
    ]
    positions = [rollback.index(command) for command in expected]
    assert positions == sorted(positions)


@pytest.mark.skipif(os.name == "nt", reason="Linux shell/runtime regression executes in Backend CI")
def test_linux_capture_filters_canaries_and_uses_restrictive_modes(tmp_path: Path):
    bash = shutil.which("bash")
    assert bash is not None
    evidence = tmp_path / "evidence"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        """#!/usr/bin/env bash
set -eu
echo 'CANARY_COMMAND_SECRET' >&2
if [[ "$1" == "ps" ]]; then
  case "$*" in *service=api*) echo api-id;; *service=web*) echo web-id;; *service=worker*) echo worker-id;; esac
elif [[ "$1" == "inspect" ]]; then
  case "$*" in
    *RestartCount*) echo 'image-id|2026-01-01T00:00:00Z|running|true|false|0|false|0|2026-01-01T00:00:01Z|0001-01-01T00:00:00Z';;
    *FailingStreak*) echo 'healthy|0|2026-01-01T00:00:01Z,2026-01-01T00:00:02Z,0';;
    *NetworkSettings.Networks*) echo 'default,network-id,172.20.0.2,api;';;
    *NetworkSettings.Ports*) echo '8000/tcp=';;
    *) echo 'running|healthy';;
  esac
elif [[ "$1" == "logs" ]]; then
  echo '2026-01-01T00:00:00Z Application startup complete CANARY_LOG_SECRET'
  for i in $(seq 1 301); do echo "2026-01-01T00:00:01Z unknown $i CANARY_LOG_SECRET"; done
elif [[ "$1" == "exec" ]]; then
  echo 'CANARY_HEALTH_SECRET'
  echo 'CANARY_HEALTH_SECRET' >&2
  exit 1
else
  echo 'CANARY_COMMAND_SECRET' >&2
  exit 1
fi
""",
        encoding="utf-8",
        newline="\n",
    )
    docker.chmod(docker.stat().st_mode | stat.S_IXUSR)
    curl = bin_dir / "curl"
    curl.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8", newline="\n")
    curl.chmod(curl.stat().st_mode | stat.S_IXUSR)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["FORENSIC_ARTIFACT_ROOT"] = str(evidence)
    result = subprocess.run(
        [
            bash,
            str(ACTIVATOR),
            "--capture-failure-evidence",
            "test-release",
            "42",
            "a" * 64,
            "vatranscribeweb",
            "https://example.invalid",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0
    artifacts = list(evidence.glob("activation-failure.test-release.*"))
    assert len(artifacts) == 1
    manifest = artifacts[0] / "manifest.txt"
    content = manifest.read_text(encoding="utf-8")
    combined = content + result.stdout + result.stderr
    assert "CANARY_LOG_SECRET" not in combined
    assert "CANARY_HEALTH_SECRET" not in combined
    assert "CANARY_COMMAND_SECRET" not in combined
    assert "api.log_event.1=" in content
    assert "api.truncated=true" in content
    assert "api.unrecognized_line_count=301" in content
    assert stat.S_IMODE(artifacts[0].stat().st_mode) == 0o700
    assert stat.S_IMODE(manifest.stat().st_mode) == 0o600


@pytest.mark.skipif(os.name == "nt", reason="Linux filesystem safety regression executes in Backend CI")
def test_linux_rejects_symlink_artifact_root_without_overwrite(tmp_path: Path):
    bash = shutil.which("bash")
    assert bash is not None
    protected = tmp_path / "protected"
    protected.mkdir()
    marker = protected / "marker"
    marker.write_text("preserve", encoding="utf-8")
    link = tmp_path / "evidence-link"
    link.symlink_to(protected, target_is_directory=True)
    env = os.environ.copy()
    env["FORENSIC_ARTIFACT_ROOT"] = str(link)
    result = subprocess.run(
        [bash, str(ACTIVATOR), "--capture-failure-evidence", "release", "9", "b" * 64, "project", "https://example.invalid"],
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 71
    assert marker.read_text(encoding="utf-8") == "preserve"
    assert list(protected.iterdir()) == [marker]


@pytest.mark.skipif(os.name == "nt", reason="Linux filesystem capacity regression executes in Backend CI")
def test_linux_capacity_preserves_existing_evidence(tmp_path: Path):
    bash = shutil.which("bash")
    assert bash is not None
    evidence = tmp_path / "evidence"
    evidence.mkdir(mode=0o700)
    for index in range(20):
        artifact = evidence / f"activation-failure.old-{index}"
        artifact.mkdir(mode=0o700)
        (artifact / "manifest.txt").write_text("preserve\n", encoding="utf-8")
    env = os.environ.copy()
    env["FORENSIC_ARTIFACT_ROOT"] = str(evidence)
    result = subprocess.run(
        [bash, str(ACTIVATOR), "--capture-failure-evidence", "release", "9", "c" * 64, "project", "https://example.invalid"],
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 72
    assert "capture skipped: capacity" in result.stderr
    assert len(list(evidence.glob("activation-failure.*"))) == 20
    assert all((path / "manifest.txt").read_text(encoding="utf-8") == "preserve\n" for path in evidence.iterdir())
