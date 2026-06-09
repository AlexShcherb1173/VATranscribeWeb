# Deploy and rollback procedure

Deploy:

```bash
PROJECT_ROOT=/srv/vatranscribe GIT_REF=main SMOKE_BASE_URL=https://vatranscribe.ru ./infra/deploy/deploy.sh
```

Rollback:

```bash
PROJECT_ROOT=/srv/vatranscribe SMOKE_BASE_URL=https://vatranscribe.ru ./infra/deploy/rollback.sh <previous-tag-or-commit>
```

Rollback does not blindly downgrade the database. Restore or Alembic downgrade requires explicit operator approval.
