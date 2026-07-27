# Stage 4 / P2-03 — Production secrets / vault

## Status

P2-03 closes the release blocker: production secrets must not live in code or in committed `.env` files.

## Implemented controls

- `SECRET_MANAGER_STRATEGY` setting.
- `RUNTIME_ENV_FILE` setting.
- `PRODUCTION_SECRETS_VALIDATION_REQUIRED` setting.
- production guardrails in API settings.
- `validate-production-secrets.sh` preflight.
- `render-runtime-env.sh` provider-neutral adapter.
- deploy/rollback integration.
- GitHub Actions handoff for `PRODUCTION_RUNTIME_ENV_FILE`.
- docs and static tests.

## Production decision

Current approved strategy:

```text
dev/local: local .env
CI/CD: GitHub Actions Secrets + GitHub Environments
production host: /opt/vatranscribe/secrets/.env.runtime
future adapters: Yandex Lockbox / Doppler / HashiCorp Vault
```

## Remaining operational task

Before public release, provision the real runtime env file on the production host and run a validation/deploy drill.
