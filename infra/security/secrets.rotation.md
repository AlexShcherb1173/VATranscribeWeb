# Production secret rotation policy

Version: `2026-06`

## Rotation intervals

| Secret | Rotation trigger | Planned interval |
|---|---|---|
| `SECRET_KEY` | suspected exposure, staff change, major release | reviewed; rotate with session invalidation plan |
| `DATABASE_URL` / `POSTGRES_PASSWORD` | suspected exposure, staff change | at least yearly |
| `YOUTUBE_COOKIES_ENCRYPTION_KEY` | suspected exposure | rotate with re-encryption plan |
| `SENTRY_DSN` | provider/project change or exposure | as needed |
| SMTP/payment secrets | provider guidance or exposure | as needed |
| Backup encryption recipient | key change or exposure | with restore drill |
| SSH deploy key | staff change or exposure | at least yearly |

## Rotation procedure

1. Create a new secret in the vault/source of truth.
2. Render `/opt/vatranscribe/secrets/.env.runtime`.
3. Run `infra/deploy/validate-production-secrets.sh`.
4. Deploy or restart affected services.
5. Run smoke tests.
6. Revoke the old secret.
7. Record the rotation event in the deployment log.

## Special cases

`SECRET_KEY` and `YOUTUBE_COOKIES_ENCRYPTION_KEY` can invalidate existing tokens or encrypted values. Rotate them only with a reviewed migration/re-encryption plan.
