# VATranscribeWeb backup and restore drill

This directory contains the operational backup/restore drill foundation for production readiness.

## Scope

Default operational drill scope:

- PostgreSQL database with `pg_dump --format=custom`.
- Checksum and manifest for every artifact.
- Optional `age` encryption for local and remote artifacts.
- Optional `rclone` remote upload.
- Disposable restore drill database: `vatranscribe_restore_drill`.

Storage/media payload backup is documented separately and is not part of the default database restore drill.

## Targets

```text
RPO: 24 hours
RTO: 2 hours
Daily retention: 14 backups
Weekly retention: 8 backups
Monthly retention: 6 backups
Restore drill frequency: monthly
```

## Production requirements

Production must set:

```bash
BACKUP_REQUIRE_ENCRYPTION=true
BACKUP_ENCRYPTION_RECIPIENT=age1...
AGE_IDENTITY_FILE=/root/.config/vatranscribe/backup-age-key.txt
BACKUP_REMOTE=rclone-remote-name
BACKUP_REMOTE_PATH=vatranscribe/postgres
```

Real keys and real backup artifacts must never be committed to Git.

## Create backup

```bash
chmod +x infra/backup/*.sh
APP_ENV=production BACKUP_REQUIRE_ENCRYPTION=true ./infra/backup/backup-postgres.sh
```

## Verify backup

```bash
./infra/backup/backup-verify.sh /backups/vatranscribe/daily/example.dump.age
```

## Restore drill

```bash
AGE_IDENTITY_FILE=/root/.config/vatranscribe/backup-age-key.txt \
  ./infra/backup/restore-drill.sh /backups/vatranscribe/daily/example.dump.age
```

The restore drill restores into a disposable database and must not overwrite the production database.
