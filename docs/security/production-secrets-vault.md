# P2-03 Production secrets / vault

## Scope

P2-03 makes production secrets explicit and deploy-blocking. The project now has:

- secret inventory;
- provider-neutral vault policy;
- runtime env file contract;
- pre-deploy secret validation;
- secret rotation policy;
- GitHub Actions handoff for production runtime env path.

## Runtime env file

Default path:

```text
/opt/vatranscribe/secrets/.env.runtime
```

The file must be created on the production host from GitHub Environments, Yandex Lockbox, Doppler, HashiCorp Vault, 1Password CLI, Docker secrets or another approved source.

## Validation

Run before deploy:

```bash
./infra/deploy/validate-production-secrets.sh /opt/vatranscribe/secrets/.env.runtime
```

The script rejects missing values, placeholder values, localhost origins, default secrets and unsafe production flags.

## Rendering

For provider-neutral rendering from environment variables:

```bash
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime ./infra/deploy/render-runtime-env.sh
```

This is a contract adapter, not a vault by itself.
