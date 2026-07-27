# Monitoring runbook

## Primary probes

- `https://vatranscribe.ru`
- `https://app.vatranscribe.ru/app/`
- `https://api.vatranscribe.ru/api/v1/health/live`
- `https://api.vatranscribe.ru/api/v1/health/ready`

## First response

1. Check Uptime Kuma alert details.
2. Check API readiness response for database/Redis/storage failures.
3. Search logs by `request_id` and service name.
4. Check Sentry release/environment for new exceptions.
5. If deployment-related, run rollback procedure from `infra/deploy/rollback.sh`.

## Useful commands

```bash
docker compose --env-file /opt/vatranscribe/secrets/.env.runtime -f docker-compose.yml -f infra/compose/docker-compose.prod.yml ps
docker compose --env-file /opt/vatranscribe/secrets/.env.runtime -f docker-compose.yml -f infra/compose/docker-compose.prod.yml logs --tail=200 api worker web
./infra/deploy/smoke-test.sh
./infra/deploy/monitoring-smoke.sh
```
