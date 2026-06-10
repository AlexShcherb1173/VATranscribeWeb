# P3-04 Monitoring / APM / logs activation checklist

This checklist closes P3-04 as production evidence, not just as code foundation.

Runtime env path: `/opt/vatranscribe/secrets/.env.runtime`.

## Uptime

- [ ] Uptime provider is selected: Uptime Kuma and/or external uptime provider.
- [ ] Checks exist for `https://vatranscribe.ru/`.
- [ ] Checks exist for `https://app.vatranscribe.ru/app/`.
- [ ] Checks exist for `https://api.vatranscribe.ru/api/v1/health/live`.
- [ ] Checks exist for `https://api.vatranscribe.ru/api/v1/health/ready`.
- [ ] Optional admin check exists for `https://admin.vatranscribe.ru/` when admin is publicly routable.
- [ ] `infra/deploy/validate-monitoring-live.sh` passes on the production host.

## Alerts

- [ ] Telegram alert channel is configured or explicitly rejected.
- [ ] email alert channel is configured or explicitly rejected.
- [ ] At least one alert delivery path is tested.
- [ ] `infra/deploy/validate-alert-delivery.sh` passes on the production host.
- [ ] Alert owner and escalation channel are recorded.

## Sentry / APM

- [ ] `APM_PROVIDER=sentry` is set in runtime env.
- [ ] `SENTRY_REQUIRED=true` is set in runtime env.
- [ ] `SENTRY_DSN` is configured from runtime secret storage.
- [ ] `SENTRY_ENVIRONMENT=production` is set.
- [ ] `RELEASE_VERSION` is set from git SHA or release tag.
- [ ] `infra/deploy/validate-sentry-test-event.sh` creates a visible Sentry event.
- [ ] Sentry event ID and marker are copied to sanitized evidence.

## Centralized logs

- [ ] `CENTRAL_LOGGING_REQUIRED=true` is set before production launch.
- [ ] Logging provider is selected: Loki/Grafana or external provider.
- [ ] API emits JSON logs.
- [ ] Nginx access/error logs are ingested.
- [ ] Worker logs are ingested.
- [ ] Logs are searchable by `request_id`, `service`, `container`, `level`, and timestamp.
- [ ] Retention is configured: Loki 14 days, Nginx access/error 30 days, audit logs 180 days.
- [ ] `infra/deploy/validate-request-id-live.sh` confirms request ID propagation.

## Evidence

- [ ] Sanitized evidence is written from `infra/monitoring/monitoring-apm-logs-evidence-template.md`.
- [ ] Evidence is stored outside Git or attached to private release notes.
- [ ] Real tokens and secrets are not copied into evidence.

## Secret handling notice

DO NOT commit real Sentry DSNs, Telegram tokens, SMTP passwords, Grafana credentials, Uptime Kuma credentials, Loki credentials, `.env.runtime` files, raw logs containing personal data, or monitoring evidence files to the repository.
