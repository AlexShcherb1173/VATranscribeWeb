# Production rehearsal deployment guide

P3-08 validates immutable release activation, migrations, smoke checks, filesystem rollback, backup/restore, and critical application flows before public launch.

DO NOT run live actions against production accidentally. `infra/deploy/run-production-rehearsal.sh` requires `REHEARSAL_ALLOW_LIVE_ACTIONS=true` before activation, migrations, rollback, or backup/restore steps mutate infrastructure.

## Required host state

- Current release path: `/opt/vatranscribe/app`.
- Runtime env: `/opt/vatranscribe/secrets/.env.runtime`.
- Runtime env is outside Git and has strict permissions.
- Immutable release archive and matching SHA-256 file are available on the rehearsal host.
- Docker and Docker Compose are installed.
- Backup, monitoring, domain/TLS/CDN, legal, and supply-chain P3 evidence workflows exist.

## Live command

```bash
cd /opt/vatranscribe/app

REHEARSAL_ALLOW_LIVE_ACTIONS=true \
RELEASE_ARCHIVE=/tmp/vatranscribe-<release-id>.tar.gz \
RELEASE_CHECKSUM=/tmp/vatranscribe-<release-id>.tar.gz.sha256 \
REHEARSAL_RELEASE_ID=<unique-release-id> \
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime \
SMOKE_BASE_URL=https://api.vatranscribe.ru \
bash infra/deploy/run-production-rehearsal.sh
```

`ROLLBACK_RELEASE_DIR` defaults to `/opt/vatranscribe/app.prev.<REHEARSAL_RELEASE_ID>` and can be supplied explicitly when rehearsing rollback to another retained release.

## Required checks

- Immutable release archive checksum and path safety validation.
- Filesystem release activation through `activate-release.sh`.
- Migrations: `python -m alembic upgrade head`.
- Smoke: `/api/v1/health/live` and `/api/v1/health/ready`.
- Rollback timing: filesystem rollback must complete in 300 seconds or less.
- Backup/restore proof: encrypted backup, manifest/checksum, disposable DB restore.
- Auth/files/jobs/billing/cookie/analytics checks.
- Monitoring/APM/logs evidence, including request_id lookup.

## Output

The script writes raw and redacted evidence under `/opt/vatranscribe/release-evidence/production-rehearsal` by default. Store evidence outside Git.
