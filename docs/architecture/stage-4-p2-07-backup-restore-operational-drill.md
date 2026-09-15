# Stage 4 P2-07 — Backup/restore operational drill

## Status

Prepared as a production-readiness foundation.

## Accepted defaults

```text
Backup remote provider: rclone/provider-neutral
Backup encryption: age placeholder
Retention: daily 14 / weekly 8 / monthly 6
RPO: 24h
RTO: 2h
Restore drill frequency: monthly
Restore target: disposable local Docker Postgres
Storage/media backup: documented, not physically tested yet
```

## Delivered controls

- PostgreSQL custom-format backup with `pg_dump --format=custom`.
- Artifact checksum with `sha256sum`.
- JSON backup manifest.
- Optional production encryption with `age`.
- Optional remote upload with `rclone`.
- Backup verification script.
- Restore drill into `vatranscribe_restore_drill`.
- Verification of `alembic_version`, critical tables and row count queries.
- Restore drill report.
- Daily backup systemd timer.
- Monthly restore drill systemd timer.
- Release documentation and static tests.

## Explicit non-goals

- Do not store real backup artifacts in Git.
- Do not store age private keys in Git.
- Do not overwrite production database during restore drill.
- Do not physically test media/storage backup in this task.
