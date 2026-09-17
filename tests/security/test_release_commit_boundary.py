"""Run the real activator and deploy scripts on an isolated Linux filesystem.

Only Docker and HTTP are faked: backup/secret validation are fixture payloads.
No production credentials, Docker daemon, or network are used.
"""

import hashlib
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import tarfile

import pytest


ROOT = Path(__file__).resolve().parents[2]
ACTIVATOR = ROOT / "infra/deploy/activate-release.sh"


def test_linux_ci_includes_commit_boundary_regressions():
    assert "tests/security/test_release_commit_boundary.py" in (
        ROOT / ".github/workflows/backend-ci.yml"
    ).read_text()


@pytest.fixture
def activation(tmp_path):
    if os.name == "nt":
        pytest.skip("Requires Linux filesystem permissions, Bash and flock")
    assert os.geteuid() != 0, "Run these permission regressions as an unprivileged user"
    app = tmp_path / "app"
    app.mkdir()
    (app / "release-marker").write_text("old")
    (app / "infra").mkdir()
    certbot = tmp_path / "certbot"
    certbot.mkdir()
    (certbot / "conf").mkdir()
    (certbot / "conf/sentinel").write_text("persistent")
    (app / "infra/certbot").symlink_to(certbot, target_is_directory=True)
    os.utime(app, (200, 200))
    runtime = tmp_path / "runtime.env"
    runtime.write_text("APP_ENV=test\n")
    evidence = tmp_path / "evidence"
    evidence.mkdir(mode=0o700)
    historical = evidence / "activation-failure.historical"
    historical.mkdir()
    (historical / "manifest.txt").write_text("preserve")
    # More failed releases than retention: all must remain intact.
    for i in range(4):
        broken = tmp_path / f"app.broken.historical-{i}"
        broken.mkdir()
        (broken / "sentinel").write_text("forensic")
    old = tmp_path / "app.prev.old"
    old.mkdir()
    (old / "release-marker").write_text("obsolete")
    os.utime(old, (100, 100))

    payload = tmp_path / "payload"
    (payload / "infra/deploy").mkdir(parents=True)
    (payload / "infra/backup").mkdir()
    (payload / "infra/compose").mkdir()
    (payload / "infra/compose/docker-compose.prod.yml").write_text("services: {}\n")
    (payload / "release-marker").write_text("candidate")
    (payload / "docker-compose.yml").write_text("services: {}\n")
    for name in ("deploy.sh", "smoke-test.sh", "monitoring-smoke.sh"):
        shutil.copyfile(ROOT / "infra/deploy" / name, payload / "infra/deploy" / name)
    (payload / "infra/deploy/validate-production-secrets.sh").write_text("exit 0\n")
    (payload / "infra/backup/backup-postgres.sh").write_text(
        'echo backup >> "$EVENTS"\nexit "${BACKUP_STATUS:-0}"\n'
    )
    archive = tmp_path / "release.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for path in payload.rglob("*"):
            if path.is_file():
                tar.add(path, arcname=str(path.relative_to(payload)))
    checksum = tmp_path / "release.tar.gz.sha256"
    checksum.write_text(hashlib.sha256(archive.read_bytes()).hexdigest() + "  release.tar.gz\n")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    events = tmp_path / "events"
    events.touch()
    docker = bindir / "docker"
    docker.write_text("""#!/bin/bash
set -eu
case "$1" in
  compose)
    marker=$(cat "$PWD/release-marker")
    printf 'compose:%s:%s\n' "$marker" "$*" >> "$EVENTS"
    if [[ "$marker" == candidate ]]; then
      case "$*" in
        *'alembic upgrade head'*) [[ "$FAIL_STAGE" != migration ]] || exit 42;;
        *'--force-recreate'*) [[ "$FAIL_STAGE" != replacement ]] || exit 43;;
      esac
    fi;;
  ps) echo candidate-api;;
  inspect)
    case "$*" in
      *RestartCount*) echo 'image|2026-01-01|running|true|false|0|false|0|2026-01-01|0';;
      *FailingStreak*) echo 'healthy|0';;
      *State.Restarting*)
        if [[ "$FAIL_STAGE" == readiness ]]; then
          echo 'running|true|false|unhealthy'
        else echo 'running|true|false|healthy'; fi;;
      *) echo 'running|healthy';;
    esac;;
  exec) echo 200;;
  logs) :;;
  *) exit 90;;
esac
""")
    docker.chmod(0o755)
    curl = bindir / "curl"
    curl.write_text("""#!/bin/bash
set -eu
printf 'http:%s\n' "$*" >> "$EVENTS"
if [[ "$FAIL_STAGE" == public && "$*" == *'/health/live'* ]]; then exit 22; fi
if [[ "$FAIL_STAGE" == monitoring && "$*" == *'https://monitor.invalid'* ]]; then exit 23; fi
exit 0
""")
    curl.chmod(0o755)

    def run(stage="", **overrides):
        env = os.environ.copy()
        env.update(
            PATH=f"{bindir}:{env['PATH']}", PROJECT_ROOT=str(app),
            CERTBOT_ROOT=str(certbot), RUNTIME_ENV_FILE=str(runtime),
            RELEASE_ID="candidate", RELEASE_RETENTION_COUNT="1",
            LOCK_FILE=str(tmp_path / "lock"), FORENSIC_ARTIFACT_ROOT=str(evidence),
            EVENTS=str(events), FAIL_STAGE=stage, RUN_MIGRATIONS="true",
            SMOKE_BASE_URL="https://public.invalid", PUBLIC_API_ORIGIN="https://public.invalid",
            UPTIME_CHECKS_BASE_URL="https://monitor.invalid",
            CHECK_DOMAIN_READINESS="false",
        )
        env.update(overrides)
        return subprocess.run(
            ["bash", str(ACTIVATOR), str(archive), str(checksum)],
            env=env, text=True, capture_output=True, timeout=20,
        )

    return run, tmp_path, app, old, certbot, evidence, events, bindir


@pytest.mark.parametrize("stage,status", [
    ("migration", 42), ("replacement", 43), ("readiness", 76),
    ("public", 22), ("monitoring", 23),
])
def test_precommit_failure_captures_original_status_and_restores_release(activation, stage, status):
    run, root, app, old, certbot, evidence, events, _ = activation
    result = run(stage)
    assert result.returncode == status, result.stderr
    assert (app / "release-marker").read_text() == "old"
    assert (root / "app.broken.candidate/release-marker").read_text() == "candidate"
    assert old.exists()
    assert "RELEASE_COMMIT_POINT" not in result.stdout
    assert "POST_COMMIT_PRUNE_" not in result.stdout + result.stderr
    assert "restoring previous release" in result.stderr
    manifests = list(evidence.glob("activation-failure.candidate.*/manifest.txt"))
    assert len(manifests) == 1
    assert f"original_activation_exit_status={status}" in manifests[0].read_text()
    assert "diagnostic_collector_result=success" in manifests[0].read_text()
    assert "compose:old:" in events.read_text()
    assert (app / "infra/certbot").resolve() == certbot


def assert_committed(result, app, root, evidence):
    assert "RELEASE_COMMIT_POINT" in result.stdout
    assert (app / "release-marker").read_text() == "candidate"
    assert not (root / "app.broken.candidate").exists()
    assert not list(evidence.glob("activation-failure.candidate.*"))
    assert "restoring previous release" not in result.stderr
    assert len(list(root.glob("app.broken.historical-*"))) == 4
    assert (evidence / "activation-failure.historical/manifest.txt").read_text() == "preserve"


def install_mount_probe(activation):
    """Model util-linux statuses and record probes and recursive rm operands."""
    _, root, _, _, _, _, _, bindir = activation
    probe_log = root / "mount-probes"
    rm_log = root / "rm-operands"
    probe_log.touch()
    rm_log.touch()
    probe = bindir / "mountpoint"
    probe.write_text(
        '#!/bin/bash\npath="${@: -1}"\n'
        f'printf "%s\\0" "$path" >> {shlex.quote(str(probe_log))}\n'
        'if [[ "$path" == "${TEST_MOUNT:-}" ]]; then exit "${PROBE_STATUS:-0}"; fi\n'
        'exit 32\n'
    )
    probe.chmod(0o755)
    rm = bindir / "rm"
    rm.write_text(
        '#!/bin/bash\nif [[ "$1" == -rf ]]; then\n'
        f'  printf "%s\\0" "${{@: -1}}" >> {shlex.quote(str(rm_log))}\n'
        'fi\n'
        f'exec {shlex.quote(shutil.which("rm"))} "$@"\n'
    )
    rm.chmod(0o755)
    return probe, probe_log, rm_log


def test_success_commits_after_all_checks_then_prunes_and_preserves_forensics(activation):
    run, root, app, old, certbot, evidence, events, _ = activation
    result = run()
    assert result.returncode == 0, result.stderr
    assert_committed(result, app, root, evidence)
    assert not old.exists()
    assert (root / "app.prev.candidate/release-marker").read_text() == "old"
    assert result.stdout.index("Monitoring smoke checks passed") < result.stdout.index("RELEASE_COMMIT_POINT")
    assert result.stdout.index("RELEASE_COMMIT_POINT") < result.stdout.index("POST_COMMIT_PRUNE_COMPLETE")
    assert (certbot / "conf/sentinel").read_text() == "persistent"
    assert events.read_text().count("backup\n") == 1


def test_real_permission_denied_after_commit_keeps_candidate_and_reports_path(activation):
    run, root, app, old, _, evidence, _, _ = activation
    protected = old / "protected"
    protected.mkdir()
    (protected / "sentinel").write_text("preserve")
    protected.chmod(0o500)
    os.utime(old, (100, 100))
    try:
        result = run()
        assert result.returncode == 1, result.stderr
        assert_committed(result, app, root, evidence)
        assert "Permission denied" in result.stderr
        assert "category=remove_failed" in result.stderr
        assert str(old) in result.stderr
        assert "candidate_active=true rollback_performed=false" in result.stderr
        assert "POST_COMMIT_PRUNE_COMPLETE" not in result.stdout
        assert (protected / "sentinel").read_text() == "preserve"
    finally:
        protected.chmod(0o700)  # Restore only this test fixture for pytest cleanup.


def test_legacy_certbot_tree_is_preserved_without_traversal(activation):
    run, root, app, old, _, evidence, _, _ = activation
    conf = old / "infra/certbot/conf"
    conf.mkdir(parents=True)
    (conf / "sentinel").write_text("historical")
    os.utime(old, (100, 100))
    _, probe_log, rm_log = install_mount_probe(activation)
    result = run()
    assert result.returncode == 73, result.stderr
    assert_committed(result, app, root, evidence)
    assert "category=legacy_certbot_state" in result.stderr
    assert (conf / "sentinel").read_text() == "historical"
    assert probe_log.read_bytes() == b""
    assert str(old).encode() not in rm_log.read_bytes().split(b"\0")


def test_pruning_unlinks_symlinks_without_deleting_external_state(activation):
    run, root, app, old, certbot, evidence, _, _ = activation
    outside = root / "outside"
    outside.mkdir()
    (outside / "sentinel").write_text("preserve")
    (old / "escape").symlink_to(outside, target_is_directory=True)
    (old / "infra").mkdir()
    (old / "infra/certbot").symlink_to(certbot, target_is_directory=True)
    (root / "app.prev.external").symlink_to(outside, target_is_directory=True)
    os.utime(old, (100, 100))
    _, probe_log, _ = install_mount_probe(activation)
    result = run()
    assert result.returncode == 0, result.stderr
    assert_committed(result, app, root, evidence)
    assert not old.exists()
    assert (outside / "sentinel").read_text() == "preserve"
    assert (certbot / "conf/sentinel").read_text() == "persistent"
    assert (root / "app.prev.external").is_symlink()
    probed = probe_log.read_bytes().split(b"\0")
    assert str(old / "infra/certbot").encode() not in probed
    assert not any(p.startswith(str(certbot).encode()) or p.startswith(str(outside).encode()) for p in probed)


def test_backup_failure_prevents_rotation_and_capture(activation):
    run, root, app, old, _, evidence, _, _ = activation
    result = run(BACKUP_STATUS="49")
    assert result.returncode == 49
    assert (app / "release-marker").read_text() == "old"
    assert old.exists()
    assert not (root / "app.broken.candidate").exists()
    assert not list(evidence.glob("activation-failure.candidate.*"))


def test_mount_boundary_is_preserved_without_running_privileged_mount(activation):
    run, root, app, old, _, evidence, _, bindir = activation
    mounted = old / "mounted"
    mounted.mkdir()
    (mounted / "sentinel").write_text("external data")
    os.utime(old, (100, 100))
    # Simulate mountpoint detection, never mount anything on the host.
    _, probe_log, rm_log = install_mount_probe(activation)
    result = run(TEST_MOUNT=str(mounted))
    assert result.returncode == 73, result.stderr
    assert_committed(result, app, root, evidence)
    assert "category=mounted_state" in result.stderr
    assert str(mounted) in result.stderr
    assert (mounted / "sentinel").read_text() == "external data"
    assert str(mounted / "sentinel").encode() not in probe_log.read_bytes().split(b"\0")
    assert str(old).encode() not in rm_log.read_bytes().split(b"\0")


def test_authoritative_nonmount_status_32_allows_ordinary_pruning(activation):
    run, root, app, old, _, evidence, _, _ = activation
    _, probe_log, rm_log = install_mount_probe(activation)
    result = run()
    assert result.returncode == 0, result.stderr
    assert_committed(result, app, root, evidence)
    assert not old.exists()
    assert str(old).encode() in probe_log.read_bytes().split(b"\0")
    assert str(old).encode() in rm_log.read_bytes().split(b"\0")
    assert "POST_COMMIT_PRUNE_COMPLETE" in result.stdout


@pytest.mark.parametrize("status", [1, 17, 126, 127])
def test_mount_probe_errors_fail_closed_despite_find_exec_success(activation, status):
    run, root, app, old, _, evidence, _, _ = activation
    target = old / "nested space\nwith newline"
    target.mkdir()
    (target / "sentinel").write_text("preserve")
    os.utime(old, (100, 100))
    probe, probe_log, rm_log = install_mount_probe(activation)
    env = dict(os.environ, TEST_MOUNT=str(target), PROBE_STATUS=str(status))
    # Reproduce H1 with actual GNU find: a failed -exec is only false, not
    # a find process error. The activator must reject this same probe failure.
    hazard = subprocess.run(
        ["find", str(target), "-maxdepth", "0", "-type", "d", "-exec",
         str(probe), "-q", "--", "{}", ";", "-prune", "-print", "-quit"],
        env=env, capture_output=True, text=True, timeout=5,
    )
    assert hazard.returncode == 0 and hazard.stdout == ""
    result = run(TEST_MOUNT=str(target), PROBE_STATUS=str(status))
    assert result.returncode == status, result.stderr
    assert_committed(result, app, root, evidence)
    assert "category=MOUNT_PROBE_ERROR" in result.stderr
    assert f"probe_status={status}" in result.stderr
    assert "nested space\\nwith newline" in result.stderr  # Bash %q escaping
    assert "candidate_active=true rollback_performed=false" in result.stderr
    assert "POST_COMMIT_PRUNE_COMPLETE" not in result.stdout
    assert "POST_COMMIT_PRUNE_REMOVED" not in result.stdout
    assert str(old).encode() not in rm_log.read_bytes().split(b"\0")
    assert str(target / "sentinel").encode() not in probe_log.read_bytes().split(b"\0")
    assert (old / "release-marker").read_text() == "obsolete"
    assert (target / "sentinel").read_text() == "preserve"


def test_enumeration_error_is_not_hidden_by_sort_or_reported_as_success(activation):
    run, root, app, old, _, evidence, _, bindir = activation
    real_find = shutil.which("find")
    probe = bindir / "find"
    probe.write_text(
        '#!/bin/bash\nif [[ "$*" == *"-maxdepth 1"* ]]; then exit 51; fi\n'
        f'exec "{real_find}" "$@"\n'
    )
    probe.chmod(0o755)
    result = run()
    assert result.returncode == 51, result.stderr
    assert_committed(result, app, root, evidence)
    assert old.exists()
    assert "category=enumeration" in result.stderr
    assert "POST_COMMIT_PRUNE_COMPLETE" not in result.stdout


def test_mount_probe_execution_failure_preserves_release(activation):
    run, root, app, old, _, evidence, _, _ = activation
    probe, _, rm_log = install_mount_probe(activation)
    # Real shell execution failure, not a mock returning the expected status.
    probe.write_text("#!/nonexistent/r14-r5-interpreter\n")
    result = run()
    assert result.returncode in (126, 127), result.stderr
    assert_committed(result, app, root, evidence)
    assert "category=MOUNT_PROBE_ERROR" in result.stderr
    assert f"probe_status={result.returncode}" in result.stderr
    assert str(old) in result.stderr
    assert "candidate_active=true rollback_performed=false" in result.stderr
    assert "POST_COMMIT_PRUNE_COMPLETE" not in result.stdout
    assert str(old).encode() not in rm_log.read_bytes().split(b"\0")
    assert (old / "release-marker").read_text() == "obsolete"


def test_mount_inspection_enumeration_error_prevents_recursive_rm(activation):
    run, root, app, old, _, evidence, _, bindir = activation
    _, _, rm_log = install_mount_probe(activation)
    real_find = shutil.which("find")
    probe = bindir / "find"
    probe.write_text(
        '#!/bin/bash\n'
        f'if [[ "$1" == -P && "$2" == {shlex.quote(str(old))} ]]; then exit 51; fi\n'
        f'exec {shlex.quote(real_find)} "$@"\n'
    )
    probe.chmod(0o755)
    result = run()
    assert result.returncode == 51, result.stderr
    assert_committed(result, app, root, evidence)
    assert "category=inspection_failed" in result.stderr
    assert str(old) in result.stderr
    assert "POST_COMMIT_PRUNE_COMPLETE" not in result.stdout
    assert str(old).encode() not in rm_log.read_bytes().split(b"\0")
    assert (old / "release-marker").read_text() == "obsolete"


def test_pruning_has_no_privilege_escalation_and_stays_on_filesystem():
    source = ACTIVATOR.read_text()
    prune = source.split("inspect_release_mounts() {", 1)[1].split("restore_previous_release()", 1)[0]
    assert "sudo" not in prune
    assert "chmod" not in prune
    assert "chown" not in prune
    assert "--one-file-system --preserve-root=all" in prune
    assert '|| true' not in prune
