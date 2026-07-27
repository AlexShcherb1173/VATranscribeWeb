# Runtime secrets / vault activation

P3-02 activates the production secret delivery model for VATranscribeWeb.

## Current strategy

For the first production activation use a local runtime env file on the production host:

```text
/opt/vatranscribe/secrets/.env.runtime
```

The repository keeps only examples, validators and runbooks. Real values stay outside Git.

## Generate manual filling template

```bash
cd /opt/vatranscribe/app
bash infra/deploy/create-runtime-env-template.sh .env.production.example /tmp/vatranscribe.env.runtime.template
```

Fill the template manually on the production host or in a password manager. Install it:

```bash
sudo mkdir -p /opt/vatranscribe/secrets
sudo chmod 700 /opt/vatranscribe/secrets
sudo install -m 600 /tmp/vatranscribe.env.runtime.template /opt/vatranscribe/secrets/.env.runtime
```

## Validate live runtime env

```bash
cd /opt/vatranscribe/app
bash infra/deploy/validate-runtime-env-live.sh /opt/vatranscribe/secrets/.env.runtime
```

Generate redacted evidence:

```bash
EVIDENCE_FILE=/tmp/vatranscribe-runtime-secrets-evidence.md \
  bash infra/deploy/validate-runtime-env-live.sh /opt/vatranscribe/secrets/.env.runtime
```

## GitHub Actions

GitHub Actions should hold deployment connection secrets only. Application runtime secrets should not be copied into workflow YAML.

Use GitHub Environment `production` with approval requirements and these secrets:

- `PRODUCTION_SSH_HOST`
- `PRODUCTION_SSH_USER`
- `PRODUCTION_SSH_KEY`
- `PRODUCTION_SSH_PORT`
- `PRODUCTION_PROJECT_ROOT`
- `PRODUCTION_RUNTIME_ENV_FILE`
- `PRODUCTION_SMOKE_BASE_URL`

## Future vault migration

The same variable names can be populated by a vault adapter later:

- Yandex Lockbox
- Doppler
- HashiCorp Vault
- 1Password CLI
- Docker secrets

The renderer `infra/deploy/render-runtime-env.sh` already accepts environment variables from any upstream secret source.

## Secret handling notice

DO NOT commit real secrets, runtime .env.runtime files, private keys, tokens, certificates, backup keys, payment keys, webhook secrets, SMTP passwords, Sentry DSNs, or redacted evidence files to the repository.
