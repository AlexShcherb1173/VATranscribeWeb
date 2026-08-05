# Stage 4 P1-06 — Backup / monitoring / CI-CD / rollback

## Scope

Adds operational production foundation:

- PostgreSQL `pg_dump` backup script.
- optional `age` backup encryption.
- local `/backups` retention: 7 daily, 4 weekly, 6 monthly.
- S3-compatible upload template via `rclone`.
- restore drill into temporary DB.
- Uptime Kuma/external uptime monitor templates.
- Sentry/APM env-driven integration.
- JSON log switch and Docker log rotation template.
- GitHub Actions production deploy workflow template.
- deploy, smoke-test and rollback scripts.

## Rollback policy

Rollback is application-first: backup the current database, rotate the current application directory to a broken-release directory, activate a retained `app.prev.*` filesystem release, recreate services, and run smoke tests. Database downgrade is not automatic.
