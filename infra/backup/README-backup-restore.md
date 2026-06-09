# VATranscribeWeb backup and restore drill

Production templates for `pg_dump`, optional `age` encryption, optional S3-compatible upload through `rclone`, local retention and restore drill.

Defaults:

```text
daily: 7
weekly: 4
monthly: 6
```

Production env values stay outside Git:

```bash
BACKUP_DIR=/backups/vatranscribe
AGE_RECIPIENT=age1...
AGE_IDENTITY_FILE=/root/.config/vatranscribe/backup-age-key.txt
S3_REMOTE=vatranscribe-s3
S3_BACKUP_PATH=vatranscribe/postgres
```

Backup:

```bash
chmod +x infra/backup/*.sh
./infra/backup/backup-postgres.sh
```

Restore drill:

```bash
AGE_IDENTITY_FILE=/root/.config/vatranscribe/backup-age-key.txt ./infra/backup/restore-drill.sh /backups/vatranscribe/daily/example.dump.age
```
