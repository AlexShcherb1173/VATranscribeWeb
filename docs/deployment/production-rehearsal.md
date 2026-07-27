# Production rehearsal deployment guide

P3-08 validates that VATranscribeWeb can be deployed, migrated, smoked, rolled back, and functionally checked before public launch.

DO NOT run live actions against production accidentally. `infra/deploy/run-production-rehearsal.sh` requires `REHEARSAL_ALLOW_LIVE_ACTIONS=true` before staging deploy, migrations, rollback, or backup/restore steps mutate infrastructure.

## Required host state

- Project path: `/opt/vatranscribe/app`.
- Runtime env: `/opt/vatranscribe/secrets/.env.runtime`.
- Runtime env is outside Git and has strict permissions.
- Docker and Docker Compose are installed.
- Backup, monitoring, domain/TLS/CDN, legal, and supply-chain P3 evidence workflows exist.

## Live command

```bash
cd /opt/vatranscribe/app

REHEARSAL_ALLOW_LIVE_ACTIONS=true     STAGING_DEPLOY_REF=<release-candidate-ref>     ROLLBACK_REF=<previous-known-good-ref>     RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime     SMOKE_BASE_URL=https://api.vatranscribe.ru     infra/deploy/run-production-rehearsal.sh
```

## Required checks

- Staging deploy from release candidate.
- Migrations: `python -m alembic upgrade head`.
- Smoke: `/api/v1/health/live` and `/api/v1/health/ready`.
- Rollback timing: rollback must complete in 300 seconds or less.
- Backup/restore proof: encrypted backup, manifest/checksum, disposable DB restore.
- Auth/files/jobs/billing/cookie/analytics checks.
- Monitoring/APM/logs evidence, including request_id lookup.

## Output

The script writes raw and redacted evidence under `/opt/vatranscribe/release-evidence/production-rehearsal` by default. Store evidence outside Git.
