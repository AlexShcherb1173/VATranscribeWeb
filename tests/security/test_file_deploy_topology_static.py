from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_workflow_builds_and_transfers_immutable_release_payload():
    workflow = read(".github/workflows/production-deploy.yml")

    assert "git archive" in workflow
    assert "sha256sum" in workflow
    assert "scp" in workflow
    assert "known_hosts" in workflow
    assert "activate-release.sh" in workflow
    assert "GIT_REF=" not in workflow
    assert "appleboy/ssh-action" not in workflow


def test_release_activator_has_atomic_rotation_and_runtime_carry_forward():
    path = ROOT / "infra/deploy/activate-release.sh"

    assert path.is_file()

    content = path.read_text(encoding="utf-8")
    data = path.read_bytes()

    assert content.startswith("#!/usr/bin/env bash")
    assert b"\r\n" not in data
    assert "sha256sum" in content
    assert "flock" in content
    assert "app.prev." in content
    assert "restore_previous_release" in content
    assert "RUNTIME_ENV_FILE" in content
    assert "CERTBOT_ROOT" in content
    assert ".p3-02-backups" in content
    assert "backup-postgres.sh" in content


def test_deploy_and_rollback_do_not_depend_on_server_git_repository():
    deploy = read("infra/deploy/deploy.sh")
    rollback = read("infra/deploy/rollback.sh")

    for content in (deploy, rollback):
        assert "git fetch" not in content
        assert "git checkout" not in content
        assert "git pull" not in content

    assert "alembic upgrade head" in deploy
    assert "app.prev." in rollback
    assert "Database downgrade is intentionally not automatic" in rollback


def test_workflow_keeps_production_environment_and_secret_boundary():
    workflow = read(".github/workflows/production-deploy.yml")

    assert "environment:" in workflow
    assert "name: production" in workflow
    assert "PRODUCTION_SSH_HOST" in workflow
    assert "PRODUCTION_SSH_USER" in workflow
    assert "PRODUCTION_SSH_KEY" in workflow
    assert "PRODUCTION_SSH_PORT" in workflow
    assert "PRODUCTION_PROJECT_ROOT" in workflow
    assert "PRODUCTION_RUNTIME_ENV_FILE" in workflow
    assert "PRODUCTION_SMOKE_BASE_URL" in workflow
    assert "PROD_SSH_KNOWN_HOSTS" in workflow


def test_release_payload_rejects_unsafe_archive_content():
    workflow = read(".github/workflows/production-deploy.yml")
    activator = read("infra/deploy/activate-release.sh")

    assert "git ls-tree -r --full-tree" in workflow
    assert "Unsupported Git entry modes" in workflow
    assert "StrictHostKeyChecking=yes" in workflow
    assert "actual_sha=" in activator
    assert "Release archive SHA-256 mismatch" in activator
    assert "Archive contains unsafe path" in activator
    assert "--no-same-owner" in activator
    assert "--no-same-permissions" in activator
    assert "Release archive contains a symbolic link" in activator
    assert "Project root must end with /app" in activator


def test_failed_release_recovery_recreates_restored_runtime():
    activator = read("infra/deploy/activate-release.sh")
    rollback = read("infra/deploy/rollback.sh")

    for content in (activator, rollback):
        assert 'local root="$1"\n  shift\n  (' in content

    assert 'restore_previous_release()' in activator
    assert 'compose_from_root "${PROJECT_ROOT}" up -d --remove-orphans --force-recreate' in activator
    assert 'restore_current_release()' in rollback
    assert 'Rollback activation failed; restoring current release.' in rollback
    assert 'compose_from_root "${PROJECT_ROOT}" build' in rollback
    assert 'compose_from_root "${PROJECT_ROOT}" up -d --remove-orphans --force-recreate' in rollback


def test_rotation_recovery_is_armed_before_second_directory_rename():
    activator = read("infra/deploy/activate-release.sh")
    rollback = read("infra/deploy/rollback.sh")

    assert (
        'mv "${PROJECT_ROOT}" "${PREVIOUS_ROOT}"\n'
        'ROTATED="true"\n'
        'mv "${STAGING_ROOT}" "${PROJECT_ROOT}"'
    ) in activator

    assert (
        'mv "${PROJECT_ROOT}" "${BROKEN_ROOT}"\n'
        'ROTATED="true"\n'
        'mv "${ROLLBACK_SOURCE}" "${PROJECT_ROOT}"'
    ) in rollback


def test_file_release_uses_reviewed_backup_force_recreate_and_bounded_retention():
    activator = read("infra/deploy/activate-release.sh")
    deploy = read("infra/deploy/deploy.sh")
    rollback = read("infra/deploy/rollback.sh")

    assert 'bash "${STAGING_ROOT}/infra/backup/backup-postgres.sh"' in activator
    assert 'bash "${PROJECT_ROOT}/infra/backup/backup-postgres.sh"' not in activator
    assert 'cd "${PROJECT_ROOT}"' in activator

    assert 'RELEASE_RETENTION_COUNT="${RELEASE_RETENTION_COUNT:-3}"' in activator
    assert "prune_release_directories()" in activator
    assert 'prune_release_directories "app.prev.*"' in activator
    assert 'prune_release_directories "app.broken.*"' in activator
    assert 'rm -rf -- "${directory}"' in activator

    assert "up -d --remove-orphans --force-recreate" in activator
    assert "up -d --remove-orphans --force-recreate" in deploy
    assert rollback.count("up -d --remove-orphans --force-recreate") == 2


def test_deploy_job_is_bound_to_the_exact_verified_commit():
    workflow = read(".github/workflows/production-deploy.yml")

    assert 'release_commit: ${{ steps.release.outputs.release_commit }}' in workflow
    assert 'id: release' in workflow
    assert 'release_commit="$(git rev-parse HEAD)"' in workflow
    assert 'ref: ${{ needs.verify.outputs.release_commit }}' in workflow
    assert workflow.count('ref: ${{ inputs.git_ref }}') == 1
    assert 'VERIFIED_RELEASE_COMMIT: ${{ needs.verify.outputs.release_commit }}' in workflow
    assert 'test "${release_commit}" = "${VERIFIED_RELEASE_COMMIT}"' in workflow


def test_force_recreate_is_scoped_to_application_services():
    activator = read("infra/deploy/activate-release.sh")
    deploy = read("infra/deploy/deploy.sh")
    rollback = read("infra/deploy/rollback.sh")

    scoped = "up -d --remove-orphans --force-recreate --no-deps api worker web"
    core = "up -d db redis"

    assert scoped in activator
    assert core in activator
    assert scoped in deploy
    assert core in deploy
    assert rollback.count(scoped) == 2
    assert rollback.count(core) == 2

    corpus = "\n".join([activator, deploy, rollback])
    force_lines = [
        line.strip()
        for line in corpus.splitlines()
        if "--force-recreate" in line
    ]

    assert len(force_lines) == 4
    assert all(line.endswith(scoped) for line in force_lines)
    assert all(" db " not in line and " redis " not in line for line in force_lines)


def test_workflow_cleans_partial_remote_payloads():
    workflow = read(".github/workflows/production-deploy.yml")

    assert "cleanup_remote_payload() {" in workflow
    assert "trap cleanup_remote_payload EXIT" in workflow
    assert "trap - EXIT" in workflow
    assert "rm -f -- %q %q %q" in workflow
    assert '"${remote_archive}"' in workflow
    assert '"${remote_checksum}"' in workflow
    assert '"${remote_activator}"' in workflow
    assert ">/dev/null 2>&1 || true" in workflow

    trap_index = workflow.index("trap cleanup_remote_payload EXIT")
    first_scp_index = workflow.index("scp -o BatchMode=yes")
    assert trap_index < first_scp_index
