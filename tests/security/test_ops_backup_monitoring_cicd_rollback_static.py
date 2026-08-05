from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_backup_scripts_include_pg_dump_encryption_retention_and_s3_template():
    backup = read("infra/backup/backup-postgres.sh")
    prune = read("infra/backup/prune-backups.sh")
    assert "pg_dump" in backup
    assert "--format=custom" in backup
    assert "AGE_RECIPIENT" in backup
    assert "age -r" in backup
    assert "rclone copy" in backup
    assert "BACKUP_RETENTION_DAILY" in backup
    assert "BACKUP_RETENTION_WEEKLY" in prune
    assert "BACKUP_RETENTION_MONTHLY" in prune


def test_restore_drill_restores_into_temporary_database_only():
    text = read("infra/backup/restore-drill.sh")
    assert "vatranscribe_restore_drill" in text
    assert "pg_restore" in text
    assert "DROP DATABASE IF EXISTS" in text
    assert "CREATE DATABASE" in text
    assert "AGE_IDENTITY_FILE" in text


def test_deploy_smoke_and_rollback_scripts_exist_with_required_guards():
    deploy = read("infra/deploy/deploy.sh")
    smoke = read("infra/deploy/smoke-test.sh")
    rollback = read("infra/deploy/rollback.sh")
    assert "backup-postgres.sh" in deploy
    assert "alembic upgrade head" in deploy
    assert "smoke-test.sh" in deploy
    assert "/api/v1/health/live" in smoke
    assert "/api/v1/health/ready" in smoke
    assert "backup-postgres.sh" in rollback
    assert "Database downgrade is intentionally not automatic" in rollback


def test_sentry_and_json_logging_are_env_driven():
    config = read("apps/api/app/config.py")
    main = read("apps/api/app/main.py")
    obs = read("apps/api/app/observability.py")
    for path in [".env.example", ".env.production.example"]:
        env = read(path)
        assert "SENTRY_DSN=" in env
        assert "SENTRY_TRACES_SAMPLE_RATE=" in env
        assert "LOG_JSON=" in env
        assert "LOG_LEVEL=" in env
        assert "RELEASE_VERSION=" in env
    assert "sentry_dsn" in config
    assert "log_json" in config
    assert "configure_logging(settings)" in main
    assert "init_sentry(settings)" in main
    assert "send_default_pii=False" in obs
    assert "JsonLogFormatter" in obs


def test_production_compose_has_docker_log_rotation_template():
    text = read("infra/compose/docker-compose.prod.yml")
    assert "x-default-json-logging" in text
    assert "driver: \"json-file\"" in text
    assert "DOCKER_LOG_MAX_SIZE" in text
    assert "DOCKER_LOG_MAX_FILE" in text
    assert text.count("logging: *default-json-logging") >= 5


def test_monitoring_docs_define_uptime_and_sentry_checks():
    uptime = read("infra/monitoring/uptime-kuma-checks.md")
    sentry = read("infra/monitoring/sentry.md")
    assert "/healthz" in uptime
    assert "/api/v1/health/live" in uptime
    assert "/api/v1/health/ready" in uptime
    assert "SENTRY_DSN" in sentry
    assert "SENTRY_TRACES_SAMPLE_RATE" in sentry


def test_github_actions_production_deploy_workflow_is_manual_and_runs_verification():
    text = read(".github/workflows/production-deploy.yml")
    assert "workflow_dispatch" in text
    assert "pytest -v" in text
    assert "npm run build:frontend" in text
    assert "docker compose -f docker-compose.yml -f infra/compose/docker-compose.prod.yml config" in text
    assert "run_deploy" in text
    assert "appleboy/ssh-action" not in text
    assert "scp " in text
    assert "activate-release.sh" in text
    assert "StrictHostKeyChecking=yes" in text
