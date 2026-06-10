# Stage 4 / P3-05 Backup restore proof

## Status

Foundation status: ready after static tests and shell syntax checks pass.  
Production-closed status: requires live encrypted backup and disposable restore drill evidence.

## Objective

P3-05 converts the backup/restore foundation into a release activation gate. The project must prove that a real encrypted PostgreSQL backup can be created and restored into a disposable database.

## Added components

- `infra/backup/run-backup-restore-proof.sh`
- `infra/backup/validate-backup-artifacts.sh`
- `infra/backup/redact-backup-restore-report.sh`
- `infra/backup/backup-restore-proof-checklist.md`
- `infra/backup/backup-restore-proof-evidence-template.md`
- `docs/deployment/backup-restore-proof.md`
- `tests/security/test_backup_restore_proof_static.py`

## Production model

Runtime env path: `/opt/vatranscribe/secrets/.env.runtime`  
Backup root: `/opt/vatranscribe/backups`

Default operational model:

- Backup scope: PostgreSQL database.
- Backup format: `pg_dump custom format`.
- Encryption: `age`.
- Local path: `/opt/vatranscribe/backups`.
- Remote upload: provider-neutral `rclone`, optional for this foundation gate.
- Restore target: disposable PostgreSQL database.
- Retention: daily 14, weekly 8, monthly 6.
- RPO: 24 hours.
- RTO: 2 hours.

## Release decision

P3-05 is not production-closed until the live server has a sanitized evidence report proving:

- encrypted artifact exists;
- checksum and manifest pass;
- restore drill passed;
- `alembic_version` and critical tables were verified;
- production database was not overwritten.

## Secret handling notice

DO NOT store real backup files, SQL dumps, `.dump.age` artifacts, age private keys, rclone configuration, cloud tokens, database credentials, runtime env files, or generated live evidence in Git.
