from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_backup_env_defines_rpo_rto_retention_and_drill_defaults():
    for path in [".env.example", ".env.production.example"]:
        env = read(path)
        assert "BACKUP_RETENTION_DAILY=14" in env
        assert "BACKUP_RETENTION_WEEKLY=8" in env
        assert "BACKUP_RETENTION_MONTHLY=6" in env
        assert "BACKUP_RPO_HOURS=24" in env
        assert "BACKUP_RTO_HOURS=2" in env
        assert "BACKUP_REQUIRE_ENCRYPTION=" in env
        assert "RESTORE_DRILL_DATABASE=vatranscribe_restore_drill" in env
        assert "RESTORE_DRILL_FREQUENCY=monthly" in env


def test_backup_script_creates_manifest_checksum_encryption_and_remote_upload():
    backup = read("infra/backup/backup-postgres.sh")
    assert "pg_dump" in backup
    assert "--format=custom" in backup
    assert "pg_restore --list" in backup
    assert "sha256sum" in backup
    assert "backup-manifest.sh" in backup
    assert "backup-verify.sh" in backup
    assert "age -r" in backup
    assert "BACKUP_REQUIRE_ENCRYPTION" in backup
    assert "BACKUP_REMOTE" in backup
    assert "rclone copy" in backup


def test_backup_verify_validates_checksum_manifest_and_restore_list():
    verify = read("infra/backup/backup-verify.sh")
    assert "sha256sum -c" in verify
    assert '"format": "pg_dump_custom"' in verify
    assert "age -d" in verify
    assert "pg_restore --list" in verify


def test_restore_drill_restores_only_disposable_database_and_verifies_schema():
    drill = read("infra/backup/restore-drill.sh")
    assert "vatranscribe_restore_drill" in drill
    assert "RESTORE_DRILL_DATABASE" in drill
    assert 'RESTORE_DRILL_DATABASE}" != "${POSTGRES_DB}' in drill
    assert "DROP DATABASE IF EXISTS" in drill
    assert "CREATE DATABASE" in drill
    assert "pg_restore" in drill
    assert "alembic_version" in drill
    assert "CRITICAL_RESTORE_TABLES" in drill
    assert "restore-drill-report.sh" in drill
    assert "RESTORE_DRILL_KEEP_DB" in drill


def test_retention_prune_covers_daily_weekly_monthly_and_metadata_files():
    prune = read("infra/backup/prune-backups.sh")
    assert "BACKUP_RETENTION_DAILY" in prune
    assert "BACKUP_RETENTION_WEEKLY" in prune
    assert "BACKUP_RETENTION_MONTHLY" in prune
    assert "*.dump.age" in prune
    assert ".manifest.json" in prune
    assert "BACKUP_RETENTION_PRUNE_REMOTE" in prune


def test_systemd_timers_define_daily_backup_and_monthly_restore_drill():
    backup_timer = read("infra/deploy/systemd/vatranscribe-backup.timer")
    drill_timer = read("infra/deploy/systemd/vatranscribe-restore-drill.timer")
    backup_service = read("infra/deploy/systemd/vatranscribe-backup.service")
    drill_service = read("infra/deploy/systemd/vatranscribe-restore-drill.service")
    assert "OnCalendar=*-*-* 03:15:00" in backup_timer
    assert "OnCalendar=monthly" in drill_timer
    assert "backup-postgres.sh" in backup_service
    assert "restore-drill.sh" in drill_service
    assert "EnvironmentFile=/opt/vatranscribe/secrets/.env.runtime" in backup_service


def test_backup_restore_docs_define_rpo_rto_safety_and_evidence():
    doc = read("docs/deployment/backup-restore-drill.md")
    arch = read("docs/architecture/stage-4-p2-07-backup-restore-operational-drill.md")
    assert "RPO: 24 hours" in doc
    assert "RTO: 2 hours" in doc
    assert "Daily: 14 backups" in doc
    assert "Weekly: 8 backups" in doc
    assert "Monthly: 6 backups" in doc
    assert "must not equal `POSTGRES_DB`" in doc
    assert "restore-drill-<timestamp>.md" in doc
    assert "Storage/media backup: documented, not physically tested yet" in arch
