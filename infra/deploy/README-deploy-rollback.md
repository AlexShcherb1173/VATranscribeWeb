# Deploy and rollback procedure

Production deployment uses an immutable `git archive` payload transferred by `.github/workflows/production-deploy.yml`.

Manual activation of an already transferred release payload:

```bash
PROJECT_ROOT=/opt/vatranscribe/app \
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime \
SMOKE_BASE_URL=https://api.vatranscribe.ru \
RELEASE_ID=<unique-release-id> \
bash /opt/vatranscribe/app/infra/deploy/activate-release.sh \
  /tmp/vatranscribe-<release-id>.tar.gz \
  /tmp/vatranscribe-<release-id>.tar.gz.sha256
```

`deploy.sh` operates only on the filesystem release already present at `PROJECT_ROOT`; it does not fetch or check out Git revisions.

Rollback to a retained filesystem release:

```bash
PROJECT_ROOT=/opt/vatranscribe/app \
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime \
SMOKE_BASE_URL=https://api.vatranscribe.ru \
bash /opt/vatranscribe/app/infra/deploy/rollback.sh \
  /opt/vatranscribe/app.prev.<release-id>
```

Rollback does not automatically downgrade the database. A restore or reviewed Alembic downgrade requires explicit operator approval.
