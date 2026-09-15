# Backup/restore operational drill

P2-07 converts the earlier backup foundation into an operational restore drill.

## Objectives

- Create PostgreSQL `pg_dump --format=custom` backups.
- Generate SHA-256 checksums and JSON manifests.
- Encrypt production backup artifacts with `age`.
- Upload artifacts through provider-neutral `rclone` remote storage.
- Restore backups into a disposable database, never production.
- Verify `alembic_version`, critical tables and row-count queries.
- Produce a monthly restore drill report.

## RPO/RTO

```text
RPO: 24 hours
RTO: 2 hours
Restore drill frequency: monthly
```

## Retention policy

```text
Daily: 14 backups
Weekly: 8 backups
Monthly: 6 backups
```

Remote lifecycle rules must match or exceed the local retention policy.

## Required production environment

```bash
BACKUP_DIR=/backups/vatranscribe
BACKUP_REQUIRE_ENCRYPTION=true
BACKUP_ENCRYPTION_RECIPIENT=age1...
AGE_IDENTITY_FILE=/root/.config/vatranscribe/backup-age-key.txt
BACKUP_REMOTE=rclone-remote-name
BACKUP_REMOTE_PATH=vatranscribe/postgres
RESTORE_DRILL_DATABASE=vatranscribe_restore_drill
RESTORE_DRILL_FREQUENCY=monthly
BACKUP_RPO_HOURS=24
BACKUP_RTO_HOURS=2
```

## Backup command

```bash
cd /srv/vatranscribe
./infra/backup/backup-postgres.sh
```

## Verification command

```bash
./infra/backup/backup-verify.sh /backups/vatranscribe/daily/<artifact>.dump.age
```

## Restore drill command

```bash
AGE_IDENTITY_FILE=/root/.config/vatranscribe/backup-age-key.txt \
  ./infra/backup/restore-drill.sh /backups/vatranscribe/daily/<artifact>.dump.age
```

If no artifact is passed, the script selects the latest daily backup.

## Safety guard

`RESTORE_DRILL_DATABASE` must not equal `POSTGRES_DB`. The script creates and drops the disposable restore database by default.

## Evidence

Each successful drill writes a report to:

```text
/backups/vatranscribe/restore-drills/restore-drill-<timestamp>.md
```

Keep the latest monthly report as release evidence.
