# P3-05 Backup restore proof checklist

This checklist closes the P3-05 foundation for VATranscribeWeb backup restore proof.

Runtime env path: `/opt/vatranscribe/secrets/.env.runtime`  
Backup root: `/opt/vatranscribe/backups`

## Production settings

- [ ] `APP_ENV=production` is active on the production host.
- [ ] `BACKUP_DIR=/opt/vatranscribe/backups` is configured.
- [ ] `BACKUP_REQUIRE_ENCRYPTION=true` is configured.
- [ ] `BACKUP_ENCRYPTION_RECIPIENT` or `AGE_RECIPIENT` is configured.
- [ ] `AGE_IDENTITY_FILE` points to a readable private age identity file outside Git.
- [ ] `RESTORE_DRILL_DATABASE=vatranscribe_restore_drill` is configured.
- [ ] `RESTORE_DRILL_DATABASE` does not equal `POSTGRES_DB`.
- [ ] `BACKUP_RETENTION_DAILY=14` is configured.
- [ ] `BACKUP_RETENTION_WEEKLY=8` is configured.
- [ ] `BACKUP_RETENTION_MONTHLY=6` is configured.
- [ ] `BACKUP_RPO_HOURS=24` is configured.
- [ ] `BACKUP_RTO_HOURS=2` is configured.

## Backup proof

- [ ] `infra/backup/run-backup-restore-proof.sh` has been executed on the production host.
- [ ] PostgreSQL backup was created with `pg_dump --format=custom`.
- [ ] The produced artifact ends with `.dump.age`.
- [ ] SHA-256 checksum file exists and passes `sha256sum -c`.
- [ ] Manifest file exists and declares `format: pg_dump_custom`.
- [ ] Manifest declares `encrypted_with_age: true`.
- [ ] Manifest checksum matches the `.sha256` file.
- [ ] `age -d` and `pg_restore --list` validation passed.

## Restore drill proof

- [ ] Backup was restored into a disposable PostgreSQL database.
- [ ] Production database was not overwritten.
- [ ] `alembic_version` query passed.
- [ ] Critical table checks passed: `alembic_version`, `users`, `jobs`, `plans`.
- [ ] Row-count queries completed.
- [ ] Disposable restore database was dropped unless `RESTORE_DRILL_KEEP_DB=true` was intentionally set.

## Evidence

- [ ] Raw restore report exists outside Git.
- [ ] Sanitized `backup-restore-proof-evidence-<timestamp>.md` exists outside Git.
- [ ] Evidence confirms RPO 24h and RTO 2h targets.
- [ ] Evidence contains no secrets, backup keys, database passwords, rclone credentials, or runtime env values.

## Secret handling notice

DO NOT commit real backup files, SQL dumps, `.dump.age` files, `.sha256` files, manifests from live production, age private keys, rclone configuration, cloud tokens, database passwords, runtime `.env.runtime` files, or generated evidence files to the repository.
