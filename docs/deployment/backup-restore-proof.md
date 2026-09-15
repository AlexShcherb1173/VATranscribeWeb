# P3-05 Backup restore proof

P3-05 verifies that VATranscribeWeb can create an encrypted production PostgreSQL backup and restore it into a disposable database without touching the production database.

Runtime env path: `/opt/vatranscribe/secrets/.env.runtime`  
Backup root: `/opt/vatranscribe/backups`

## Scope

- PostgreSQL database backup.
- `pg_dump --format=custom` artifact.
- `age` encryption.
- SHA-256 checksum.
- JSON manifest.
- Disposable restore drill database.
- Sanitized restore proof report.

Storage/media backup is documented separately and is not accepted as a substitute for the P3-05 database restore proof.

## Required production env

```bash
APP_ENV=production
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime
BACKUP_DIR=/opt/vatranscribe/backups
BACKUP_REQUIRE_ENCRYPTION=true
BACKUP_ENCRYPTION_RECIPIENT=age1...
AGE_IDENTITY_FILE=/root/.config/vatranscribe/backup-age-key.txt
RESTORE_DRILL_DATABASE=vatranscribe_restore_drill
BACKUP_RPO_HOURS=24
BACKUP_RTO_HOURS=2
BACKUP_RETENTION_DAILY=14
BACKUP_RETENTION_WEEKLY=8
BACKUP_RETENTION_MONTHLY=6
```

## Run full proof

```bash
cd /opt/vatranscribe/app
chmod +x infra/backup/*.sh
APP_ENV=production       RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime       BACKUP_DIR=/opt/vatranscribe/backups       infra/backup/run-backup-restore-proof.sh
```

## Validate backup artifact manually

```bash
infra/backup/validate-backup-artifacts.sh /opt/vatranscribe/backups/daily/<artifact>.dump.age
```

## Redact restore report manually

```bash
infra/backup/redact-backup-restore-report.sh       /opt/vatranscribe/backups/restore-drills/restore-drill-<timestamp>.md       /opt/vatranscribe/backups/evidence/backup-restore-proof-evidence-<timestamp>.md
```

## Acceptance criteria

- Backup artifact is encrypted as `.dump.age`.
- Checksum passes with `sha256sum -c`.
- Manifest declares `pg_dump_custom` and `encrypted_with_age: true`.
- `age -d` and `pg_restore --list` pass.
- Restore drill uses `RESTORE_DRILL_DATABASE`, not `POSTGRES_DB`.
- `alembic_version` and critical tables are verified.
- Sanitized evidence exists outside Git.

## Secret handling notice

DO NOT commit backup artifacts, SQL dumps, age keys, rclone configuration, cloud credentials, runtime env files, or generated restore evidence to Git.
