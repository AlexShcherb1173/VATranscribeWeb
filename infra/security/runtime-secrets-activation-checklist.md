# Runtime secrets activation checklist

This checklist closes P3-02 only when the runtime secrets exist outside Git and have been validated on the production host.

## Strategy

Current strategy: `runtime-env-file`.

Production runtime env path:

```text
/opt/vatranscribe/secrets/.env.runtime
```

Production deploy path:

```text
/opt/vatranscribe/app
```

Future vault adapters are documented but not activated yet:

- Yandex Lockbox
- Doppler
- HashiCorp Vault
- 1Password CLI
- Docker secrets

## Required host setup

```bash
sudo mkdir -p /opt/vatranscribe/secrets
sudo chown deploy:deploy /opt/vatranscribe/secrets
sudo chmod 700 /opt/vatranscribe/secrets
sudo install -m 600 .env.runtime /opt/vatranscribe/secrets/.env.runtime
```

## Manual secret filling rules

- Do not commit `.env.runtime`.
- Do not send `.env.runtime` to ChatGPT.
- Do not paste values into issues, logs, screenshots or PRs.
- Use generated templates only as filling guides.
- Replace every `CHANGE_ME`, `example.com`, `localhost`, `super-secret`, and `local-dev` value.

## Required validation

Run on production host:

```bash
cd /opt/vatranscribe/app
bash infra/deploy/validate-runtime-env-live.sh /opt/vatranscribe/secrets/.env.runtime
```

Generate redacted evidence:

```bash
cd /opt/vatranscribe/app
EVIDENCE_FILE=/tmp/vatranscribe-runtime-secrets-evidence.md \
  bash infra/deploy/validate-runtime-env-live.sh /opt/vatranscribe/secrets/.env.runtime
```

Only the redacted evidence file may be shared for audit.

## P3-02 closure criteria

- Runtime env exists outside repository.
- File permissions are `600` or stricter.
- `validate-production-secrets.sh` passes.
- Redacted evidence has `PLACEHOLDER_COUNT=0`.
- GitHub `production` environment exists.
- Required GitHub environment secrets are present.
- Runtime secret rotation owner and schedule are documented.
