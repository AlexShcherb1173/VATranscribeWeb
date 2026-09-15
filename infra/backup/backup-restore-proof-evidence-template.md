# P3-05 Backup restore proof evidence

Status: NOT EXECUTED
Environment: ____________________
Captured at UTC: ____________________
Operator: ____________________

DO NOT include database credentials, encryption keys, raw runtime environment contents, backup payloads, or unredacted host paths in this evidence.

Runtime secret source:
- `/opt/vatranscribe/secrets/.env.runtime`

Backup location:
- `/opt/vatranscribe/backups`

## Backup artifact

- `pg_dump` result: ____________________
- Encrypted with `age`: ____________________
- SHA-256 checksum: ____________________
- Manifest: ____________________
- Backup age: ____________________

## Disposable restore

- Disposable database: ____________________
- Restore result: PASS / FAIL
- `alembic_version`: ____________________

## Recovery objectives

- Observed RPO: ____________________
- Observed RTO: ____________________

Final result: PASS / FAIL
