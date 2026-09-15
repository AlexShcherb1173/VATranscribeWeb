# Production secret inventory

## Required in production

| Variable | Category | Notes |
|---|---|---|
| `APP_ENV` | runtime | Must be `production`. |
| `SECRET_MANAGER_STRATEGY` | runtime | Must not be `local-env`. |
| `RUNTIME_ENV_FILE` | runtime | `/opt/vatranscribe/secrets/.env.runtime`. |
| `PRODUCTION_SECRETS_VALIDATION_REQUIRED` | runtime | Must be `true`. |
| `SECRET_KEY` | secret | JWT/signing/encryption derivation. Rotate carefully. |
| `DATABASE_URL` | secret | PostgreSQL connection string. |
| `POSTGRES_PASSWORD` | secret | Database password. |
| `REDIS_URL` | secret-ish | Redis connection. |
| `CELERY_BROKER_URL` | secret-ish | Celery broker. |
| `CELERY_RESULT_BACKEND` | secret-ish | Celery result backend. |
| `CORS_ORIGINS` | security config | HTTPS origins only. |
| `PUBLIC_API_ORIGIN` | public runtime | HTTPS production origin. |
| `VITE_API_BASE_URL` | public build | HTTPS API base. |
| `YOUTUBE_COOKIES_ENCRYPTION_KEY` | secret | Fernet key for per-user YouTube cookies. |
| `BACKUP_ENCRYPTION_RECIPIENT` / `AGE_RECIPIENT` | secret/config | Backup encryption recipient. |
| `LEGAL_OPERATOR_NAME` | legal config | Real production value. |
| `LEGAL_CONTACT_EMAIL` | legal config | Monitored mailbox. |
| `PRIVACY_CONTACT_EMAIL` | legal config | Monitored mailbox. |
| `ADMIN_2FA_REQUIRED` | security config | Must be `true`. |
| `ADMIN_2FA_ISSUER` | security config | Real issuer name. |
| `TRUSTED_PROXY_CIDRS` | security config | Real reverse-proxy CIDRs. |
| `RATE_LIMIT_REDIS_FAIL_OPEN` | security config | Must be `false`. |

## Optional sensitive variables

| Variable | Required when |
|---|---|
| `SENTRY_DSN` | APM is enabled. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` | Email provider is enabled. |
| `PAYMENT_PROVIDER`, `PAYMENT_WEBHOOK_SECRET`, `PAYMENT_API_KEY` | Payments are enabled. |
| `BACKUP_REMOTE`, `BACKUP_REMOTE_PATH` | Remote backup storage is enabled. |

## Public/non-secret but production-required

Public URLs and legal variables are not secrets, but production must still reject placeholders.
