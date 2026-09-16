import os
from pathlib import Path
import shutil
import stat
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "infra/deploy/deploy.sh"
ACTIVATOR = ROOT / "infra/deploy/activate-release.sh"
SMOKE = ROOT / "infra/deploy/smoke-test.sh"
BACKEND_CI = ROOT / ".github/workflows/backend-ci.yml"


def deploy_source() -> str:
    return DEPLOY.read_text(encoding="utf-8")


def test_gate_has_frozen_identity_single_deadline_and_exact_insertion_point():
    text = deploy_source()
    assert "READINESS_POLL_INTERVAL_SECONDS=5" in text
    assert "READINESS_TIMEOUT_SECONDS=175" in text
    assert text.count("deadline=$((started_at + READINESS_TIMEOUT_SECONDS))") == 1
    assert 'label=com.docker.compose.project=${PROJECT_NAME}' in text
    assert "label=com.docker.compose.service=api" in text
    assert "docker ps -aq --no-trunc" in text
    assert 'frozen_candidate_id="${candidate_ids[0]}"' in text
    assert '[[ "${candidate_ids[0]}" != "${frozen_candidate_id}" ]]' in text
    replacement = "up -d --remove-orphans --force-recreate --no-deps api worker web"
    gate = "wait_for_candidate_api_readiness"
    smoke = "bash ./infra/deploy/smoke-test.sh"
    assert text.rindex(replacement) < text.rindex(gate) < text.rindex(smoke)


def test_gate_is_bounded_and_has_stable_failure_contract():
    text = deploy_source()
    body = text[text.index("wait_for_candidate_api_readiness() {") : text.index("\n}\n\ncd ")]
    assert "command -v timeout" in body
    assert body.count("timeout --signal=TERM --kill-after=2s") == 3
    assert '"${remaining}s"' in body
    assert "API_READINESS_TIMEOUT" in body
    assert "return 124" in body
    expected = {
        "API_READINESS_TOOL_UNAVAILABLE": "70",
        "API_READINESS_IDENTITY_MISSING": "71",
        "API_READINESS_IDENTITY_AMBIGUOUS": "72",
        "API_READINESS_IDENTITY_CHANGED": "73",
        "API_READINESS_HEALTHCHECK_MISSING": "74",
        "API_READINESS_CONTAINER_TERMINAL": "75",
        "API_READINESS_UNHEALTHY": "76",
        "API_READINESS_INSPECT_FAILURE": "77",
        "API_READINESS_READY_UNEXPECTED_STATUS": "78",
        "API_READINESS_READY_PROBE_FAILURE": "79",
    }
    for category, status in expected.items():
        at = body.index(category)
        assert f"return {status}" in body[at : at + 400]
    assert 'sleep_seconds="${READINESS_POLL_INTERVAL_SECONDS}"' in body
    assert "if (( remaining < sleep_seconds ))" in body
    assert 'sleep "${sleep_seconds}"' in body
    assert "sleep 5" not in text


def test_lifecycle_and_internal_ready_state_machine_is_fail_closed():
    text = deploy_source()
    assert "{{.State.Status}}|{{.State.Running}}|{{.State.Restarting}}" in text
    assert "{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}" in text
    assert '"${running_status}" != "true"' in text
    assert '"${restarting_status}" != "false"' in text
    assert '"${lifecycle_status}" != "running"' in text
    for state in ("missing)", "unhealthy)", "starting)", "healthy)"):
        assert state in text
    assert "docker exec --user 10001:10001" in text
    assert "http://127.0.0.1:8000/api/v1/health/ready" in text
    assert "response.close()" in text
    assert "print(status)" in text
    assert "200)" in text
    assert "503)" in text
    assert "API_READINESS_READY_UNEXPECTED_STATUS" in text


def test_readiness_logging_is_normalized_and_discards_sensitive_outputs():
    text = deploy_source()
    body = text[text.index("wait_for_candidate_api_readiness() {") : text.index("\n}\n\ncd ")]
    assert "category=%s candidate_id=%s lifecycle=%s health=%s elapsed_seconds=%s" in text
    assert "{{json" not in body
    assert ".Config.Env" not in body
    assert "response.read" not in body
    assert "print(exc" not in body
    assert body.count("2>/dev/null") >= 5
    assert "docker inspect" in body
    assert "docker exec" in body


def test_existing_deployment_smoke_and_failure_contracts_remain_intact():
    deploy = deploy_source()
    smoke = SMOKE.read_text(encoding="utf-8")
    activator = ACTIVATOR.read_text(encoding="utf-8")
    assert deploy.count("bash ./infra/deploy/smoke-test.sh") == 1
    assert deploy.count("bash ./infra/deploy/monitoring-smoke.sh") == 1
    assert "curl --fail --silent --show-error" in smoke
    assert "--retry" not in smoke
    cleanup = activator[activator.index("cleanup() {") : activator.index("\n}\n\ntrap cleanup EXIT")]
    assert cleanup.index("local status=$?") < cleanup.index("setsid sh -c")
    assert cleanup.index("setsid sh -c") < cleanup.index("restore_previous_release || true")
    assert cleanup.index("restore_previous_release || true") < cleanup.index('exit "${status}"')
    assert "diagnostic_status=$?" in cleanup
    assert 'exit "${diagnostic_status}"' not in cleanup


def test_existing_backup_migration_and_replacement_order_is_unchanged():
    text = deploy_source()
    expected = [
        'bash ./infra/backup/backup-postgres.sh',
        "run --rm api python -m alembic upgrade head",
        "up -d db redis",
        "up -d --remove-orphans --force-recreate --no-deps api worker web",
        "wait_for_candidate_api_readiness",
        "bash ./infra/deploy/smoke-test.sh",
        "bash ./infra/deploy/monitoring-smoke.sh",
    ]
    positions = [text.rindex(item) for item in expected]
    assert positions == sorted(positions)


def test_backend_ci_routes_readiness_test_in_existing_linux_job_once():
    workflow = BACKEND_CI.read_text(encoding="utf-8")
    assert "docker-api-build:" in workflow
    assert "runs-on: ubuntu-latest" in workflow
    assert "Validate deployment filesystem regressions" in workflow
    assert workflow.count("tests/security/test_deploy_api_readiness_gate.py") == 1
    for existing in (
        "test_release_activation_filemode_static.py",
        "test_backup_runtime_env_propagation_static.py",
        "test_backup_restore_drill_static.py",
        "test_release_failure_evidence_capture.py",
    ):
        assert workflow.count(existing) == 1


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


@pytest.fixture
def linux_deploy_harness(tmp_path: Path):
    if os.name == "nt":
        pytest.skip("Linux shell/runtime regression executes in Backend CI")
    real_bash = shutil.which("bash")
    assert real_bash is not None
    bin_dir = tmp_path / "bin"
    state_dir = tmp_path / "state"
    project = tmp_path / "project"
    bin_dir.mkdir()
    state_dir.mkdir()
    project.mkdir()
    (state_dir / "clock").write_text("0\n", encoding="utf-8")
    _write_executable(
        bin_dir / "timeout",
        "#!/bin/sh\nshift\nshift\nshift\nexec \"$@\"\n",
    )
    _write_executable(
        bin_dir / "date",
        "#!/bin/sh\ncat \"$STATE_DIR/clock\"\n",
    )
    _write_executable(
        bin_dir / "sleep",
        "#!/bin/sh\nread now < \"$STATE_DIR/clock\"\nnow=$((now + $1))\nprintf '%s\\n' \"$now\" > \"$STATE_DIR/clock\"\nprintf 'sleep:%s\\n' \"$1\" >> \"$STATE_DIR/events\"\n",
    )
    _write_executable(
        bin_dir / "bash",
        "#!/bin/sh\nprintf 'bash:%s\\n' \"$*\" >> \"$STATE_DIR/events\"\ncase \"$1\" in *smoke-test.sh) [ \"${SMOKE_FAIL:-0}\" = 0 ] || exit 88;; esac\nexit 0\n",
    )
    _write_executable(
        bin_dir / "docker",
        """#!/usr/bin/env python3
import os
from pathlib import Path
import sys

state = Path(os.environ["STATE_DIR"])
args = sys.argv[1:]

def log(value):
    with (state / "events").open("a", encoding="utf-8") as handle:
        handle.write(value + "\\n")

def next_value(name, default):
    values = os.environ.get(name, default).split(";")
    counter = state / (name + ".count")
    index = int(counter.read_text() if counter.exists() else "0")
    counter.write_text(str(index + 1), encoding="utf-8")
    return values[min(index, len(values) - 1)]

if args[0] == "compose":
    log("docker:" + " ".join(args))
elif args[0] == "ps":
    value = next_value("PS_SEQUENCE", "candidate-full-id")
    if value:
        print(value.replace(",", "\\n"))
    if os.environ.get("READINESS_STDERR"):
        print(os.environ["READINESS_STDERR"], file=sys.stderr)
elif args[0] == "inspect":
    value = next_value("INSPECT_SEQUENCE", "running|true|false|healthy")
    if os.environ.get("READINESS_STDERR"):
        print(os.environ["READINESS_STDERR"], file=sys.stderr)
    if value == "fail":
        raise SystemExit(9)
    print(value)
elif args[0] == "exec":
    value = next_value("READY_SEQUENCE", "200")
    if os.environ.get("READINESS_STDERR"):
        print(os.environ["READINESS_STDERR"], file=sys.stderr)
    if value == "fail":
        raise SystemExit(10)
    print(value)
else:
    raise SystemExit(11)
""",
    )

    def run(**overrides):
        for counter in state_dir.glob("*.count"):
            counter.unlink()
        (state_dir / "clock").write_text("0\n", encoding="utf-8")
        (state_dir / "events").write_text("", encoding="utf-8")
        env = os.environ.copy()
        env.update(
            {
                "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
                "STATE_DIR": str(state_dir),
                "PROJECT_ROOT": str(project),
                "RUNTIME_ENV_FILE": str(tmp_path / "runtime.env"),
                "PROJECT_NAME": "readiness-test",
                "BACKUP_BEFORE_DEPLOY": "false",
                "RUN_MIGRATIONS": "true",
            }
        )
        env.update({key: str(value) for key, value in overrides.items()})
        result = subprocess.run(
            [real_bash, str(DEPLOY)],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        events = (state_dir / "events").read_text(encoding="utf-8").splitlines()
        return result, events, int((state_dir / "clock").read_text())

    return run, bin_dir, state_dir, project, real_bash


def _smoke_events(events):
    return [event for event in events if "smoke-test.sh" in event]


def test_linux_starting_then_healthy_and_ready_200_runs_smoke(linux_deploy_harness):
    run, *_ = linux_deploy_harness
    result, events, clock = run(
        INSPECT_SEQUENCE="running|true|false|starting;running|true|false|healthy",
        READY_SEQUENCE="200",
    )
    assert result.returncode == 0
    assert clock == 5
    assert events.index("sleep:5") < events.index("bash:./infra/deploy/smoke-test.sh")
    assert len(_smoke_events(events)) == 1


def test_linux_ready_503_then_200_uses_same_budget_and_runs_smoke(linux_deploy_harness):
    run, *_ = linux_deploy_harness
    result, events, clock = run(READY_SEQUENCE="503;200")
    assert result.returncode == 0
    assert clock == 5
    assert len(_smoke_events(events)) == 1
    assert "API_READINESS_PASS" in result.stderr


def test_linux_repeated_503_reaches_single_global_deadline(linux_deploy_harness):
    run, *_ = linux_deploy_harness
    result, events, clock = run(READY_SEQUENCE="503")
    assert result.returncode == 124
    assert clock == 175
    assert not _smoke_events(events)
    assert "API_READINESS_TIMEOUT" in result.stderr
    assert "elapsed_seconds=175" in result.stderr


@pytest.mark.parametrize(
    ("inspect", "status", "category"),
    [
        ("running|true|false|unhealthy", 76, "API_READINESS_UNHEALTHY"),
        ("exited|false|false|unhealthy", 75, "API_READINESS_CONTAINER_TERMINAL"),
        ("dead|false|false|unhealthy", 75, "API_READINESS_CONTAINER_TERMINAL"),
        ("restarting|true|true|starting", 75, "API_READINESS_CONTAINER_TERMINAL"),
        ("running|true|false|missing", 74, "API_READINESS_HEALTHCHECK_MISSING"),
        ("fail", 77, "API_READINESS_INSPECT_FAILURE"),
    ],
)
def test_linux_lifecycle_failures_prevent_smoke(linux_deploy_harness, inspect, status, category):
    run, *_ = linux_deploy_harness
    result, events, _ = run(INSPECT_SEQUENCE=inspect)
    assert result.returncode == status
    assert category in result.stderr
    assert not _smoke_events(events)


@pytest.mark.parametrize(
    ("ps_sequence", "status", "category"),
    [
        ("", 71, "API_READINESS_IDENTITY_MISSING"),
        ("one,two", 72, "API_READINESS_IDENTITY_AMBIGUOUS"),
        ("original;replacement", 73, "API_READINESS_IDENTITY_CHANGED"),
    ],
)
def test_linux_identity_failures_prevent_smoke(linux_deploy_harness, ps_sequence, status, category):
    run, *_ = linux_deploy_harness
    result, events, _ = run(PS_SEQUENCE=ps_sequence)
    assert result.returncode == status
    assert category in result.stderr
    assert not _smoke_events(events)


@pytest.mark.parametrize(
    ("ready", "status", "category"),
    [
        ("418", 78, "API_READINESS_READY_UNEXPECTED_STATUS"),
        ("fail", 79, "API_READINESS_READY_PROBE_FAILURE"),
    ],
)
def test_linux_ready_failures_are_immediate_and_safe(linux_deploy_harness, ready, status, category):
    run, *_ = linux_deploy_harness
    canary = "SECRET_RAW_COMMAND_OUTPUT"
    result, events, clock = run(READY_SEQUENCE=ready, READINESS_STDERR=canary)
    assert result.returncode == status
    assert category in result.stderr
    assert clock == 0
    assert canary not in result.stdout + result.stderr
    assert not _smoke_events(events)


def test_linux_public_smoke_failure_remains_authoritative(linux_deploy_harness):
    run, *_ = linux_deploy_harness
    result, events, _ = run(SMOKE_FAIL="1")
    assert result.returncode == 88
    assert len(_smoke_events(events)) == 1


def test_linux_migration_replacement_readiness_smoke_order(linux_deploy_harness):
    run, *_ = linux_deploy_harness
    result, events, _ = run()
    assert result.returncode == 0
    migration = next(i for i, event in enumerate(events) if "run --rm api alembic upgrade head" in event)
    replacement = next(i for i, event in enumerate(events) if "--force-recreate --no-deps api worker web" in event)
    smoke = events.index("bash:./infra/deploy/smoke-test.sh")
    assert migration < replacement < smoke


def test_linux_missing_timeout_tool_fails_before_smoke(linux_deploy_harness):
    _, bin_dir, state_dir, project, real_bash = linux_deploy_harness
    (bin_dir / "timeout").unlink()
    _write_executable(bin_dir / "ln", "#!/bin/sh\nexit 0\n")
    _write_executable(
        bin_dir / "docker",
        "#!/bin/sh\nprintf 'docker:%s\\n' \"$*\" >> \"$STATE_DIR/events\"\nexit 0\n",
    )
    env = {
        "PATH": str(bin_dir),
        "STATE_DIR": str(state_dir),
        "PROJECT_ROOT": str(project),
        "RUNTIME_ENV_FILE": str(project / "runtime.env"),
        "PROJECT_NAME": "readiness-test",
        "BACKUP_BEFORE_DEPLOY": "false",
        "RUN_MIGRATIONS": "true",
    }
    result = subprocess.run(
        [real_bash, str(DEPLOY)], env=env, capture_output=True, text=True, timeout=5, check=False
    )
    events = (state_dir / "events").read_text(encoding="utf-8").splitlines()
    assert result.returncode == 70
    assert "API_READINESS_TOOL_UNAVAILABLE" in result.stderr
    assert not _smoke_events(events)
