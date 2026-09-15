# Production secrets / vault policy

## Decision

VATranscribeWeb uses a provider-neutral production secret model for P2-03:

- local development: `.env` only on the developer machine;
- CI/CD: GitHub Actions Secrets plus GitHub Environments;
- production host: `/opt/vatranscribe/secrets/.env.runtime`;
- future adapters: Yandex Lockbox, Doppler, HashiCorp Vault, 1Password CLI or Docker secrets.

Real production secrets must never be committed to Git. `.env.production.example` is a template only.

## Required production controls

- `APP_ENV=production`
- `SECRET_MANAGER_STRATEGY=runtime-env-file` or a supported vault adapter
- `RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime`
- `PRODUCTION_SECRETS_VALIDATION_REQUIRED=true`
- pre-deploy validation through `infra/deploy/validate-production-secrets.sh`
- runtime env file permissions: directory `0700`, file `0600`

## Forbidden in production

- `SECRET_MANAGER_STRATEGY=local-env`
- `SECRET_KEY=super-secret-key-change-me`
- any `CHANGE_ME`, `example.com`, `localhost`, `local-dev` or placeholder secret values
- `DATABASE_URL` with `postgres:postgres`
- `RATE_LIMIT_REDIS_FAIL_OPEN=true`
- `ADMIN_2FA_REQUIRED=false`
- plaintext production `.env` committed into the repository

## Deploy flow

1. Provision `/opt/vatranscribe/secrets/.env.runtime` on the production host.
2. Run `infra/deploy/validate-production-secrets.sh`.
3. Deploy using `infra/deploy/deploy.sh`.
4. The deploy script symlinks `.env` to the runtime file and also passes `--env-file` to Docker Compose.
5. Smoke tests run after deployment.

## Vault adapters

Provider adapters are intentionally out of scope for P2-03 implementation. The supported handoff contract is: a vault tool renders environment variables, then `render-runtime-env.sh` writes the runtime env file with restricted permissions.
