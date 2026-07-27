# Stage 4 / P3-04 Monitoring / APM / logs activation

## Goal

P3-04 converts the monitoring foundation into an evidence-driven production activation workflow.

Runtime env path: `/opt/vatranscribe/secrets/.env.runtime`.

## Decisions

- Uptime provider: Uptime Kuma for self-hosted checklist plus external provider documentation.
- Alert channels: Telegram and email.
- APM provider: Sentry.
- Sentry test event: dedicated validation script.
- Logging provider: Loki/Grafana optional overlay, with documented external-provider alternative.
- Request ID: required end-to-end through nginx, API response headers, API JSON logs, and centralized search.
- Retention: Loki 14 days, Nginx access/error logs 30 days, audit logs 180 days.

## Added operational assets

- `infra/deploy/validate-monitoring-live.sh`
- `infra/deploy/validate-alert-delivery.sh`
- `infra/deploy/validate-sentry-test-event.sh`
- `infra/deploy/validate-request-id-live.sh`
- `infra/monitoring/monitoring-apm-logs-activation-checklist.md`
- `infra/monitoring/monitoring-apm-logs-evidence-template.md`
- `infra/monitoring/uptime-kuma-production-checks.md`
- `infra/monitoring/alert-delivery-check.md`
- `infra/monitoring/sentry-test-event.md`
- `infra/monitoring/request-id-log-search-check.md`

## Production-closed criteria

P3-04 can be marked production-closed only after live evidence proves:

1. uptime monitors exist and are green;
2. Telegram or email alert delivery works;
3. Sentry test event is visible in the production project;
4. logs are searchable by `request_id`;
5. retention settings are recorded;
6. sanitized evidence exists outside Git.

## Secret handling notice

DO NOT commit Sentry DSNs, Telegram tokens, SMTP credentials, Grafana credentials, Uptime Kuma credentials, Loki credentials, `.env.runtime`, raw logs, or filled evidence files.
