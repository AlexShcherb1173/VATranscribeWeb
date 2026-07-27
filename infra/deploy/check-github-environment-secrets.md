# GitHub Environment secrets checklist

Environment: `production`.

Do not store real runtime application secrets in repository files. The deployment workflow should only receive the SSH connection and runtime file location. Application secrets stay on the production host in `/opt/vatranscribe/secrets/.env.runtime` or in a future vault provider.

## Required GitHub Environment secrets

| Secret | Purpose | Required |
|---|---|---:|
| `PRODUCTION_SSH_HOST` | Production host address | yes |
| `PRODUCTION_SSH_USER` | SSH user for deploy | yes |
| `PRODUCTION_SSH_KEY` | Private SSH key for deploy | yes |
| `PRODUCTION_SSH_PORT` | SSH port, usually `22` | yes |
| `PRODUCTION_PROJECT_ROOT` | Deploy path, default `/opt/vatranscribe/app` | yes |
| `PRODUCTION_RUNTIME_ENV_FILE` | Runtime env path, default `/opt/vatranscribe/secrets/.env.runtime` | yes |
| `PRODUCTION_SMOKE_BASE_URL` | Public HTTPS base URL for smoke checks | yes |

## Environment protection rules

- Require manual approval for `production` deploys.
- Limit who can update production secrets.
- Rotate SSH deploy key after staff/device changes.
- Never paste `.env.runtime` contents into GitHub logs, issues, pull requests or ChatGPT.
- Keep runtime application secrets either on the host or in a vault provider, not in workflow YAML.

## Evidence to capture

- Screenshot or exported checklist showing that the `production` environment exists.
- Redacted list of configured secret names, without secret values.
- Successful run of `infra/deploy/validate-runtime-env-live.sh` on the host.
- Successful `infra/deploy/smoke-test.sh` after deployment.
