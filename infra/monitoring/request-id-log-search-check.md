# Request ID log-search check

Runtime env path: `/opt/vatranscribe/secrets/.env.runtime`.

P3-04 requires end-to-end `request_id` propagation and log search.

The expected flow is:

```text
client -> nginx X-Request-ID -> API response header -> API JSON log -> centralized log provider
```

Run:

```bash
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime ./infra/deploy/validate-request-id-live.sh
```

The script sends a unique `X-Request-ID` to:

```text
https://api.vatranscribe.ru/api/v1/health/live
```

Then search logs with one of these queries.

Loki/Grafana examples:

```text
{service="api"} |= "<request_id>"
{container="vatranscribe-api"} |= "<request_id>"
```

Docker fallback:

```bash
docker compose --env-file /opt/vatranscribe/secrets/.env.runtime   -f docker-compose.yml   -f infra/compose/docker-compose.prod.yml   logs --since=10m api | grep '<request_id>'
```

Production release requires centralized provider evidence, not only Docker fallback.

## Secret handling notice

DO NOT commit raw logs containing personal data, provider credentials, `.env.runtime`, or filled request-id evidence to the repository.
