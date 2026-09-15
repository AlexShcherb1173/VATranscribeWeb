# Monitoring / APM / logs activation

This document describes P3-04 activation for VATranscribeWeb.

Runtime env path: `/opt/vatranscribe/secrets/.env.runtime`.

## Scope

P3-04 activates:

- Uptime Kuma or external uptime checks.
- Telegram/email alert delivery.
- Sentry/APM test event.
- Loki/Grafana or external centralized logging provider.
- `X-Request-ID` propagation and log search.
- Retention evidence: Loki 14 days, Nginx 30 days, audit logs 180 days.

## Runtime settings

Recommended production runtime settings:

```env
MONITORING_REQUIRED=true
MONITORING_RELEASE_CHECKLIST_ACK=true
UPTIME_PROVIDER=uptime-kuma
UPTIME_ALERT_CHANNELS=telegram,email
UPTIME_CHECKS_BASE_URL=https://vatranscribe.ru
APM_PROVIDER=sentry
SENTRY_REQUIRED=true
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.05
CENTRAL_LOGGING_REQUIRED=true
CENTRAL_LOGGING_PROVIDER=loki
LOG_JSON=true
LOG_RETENTION_DAYS=30
LOKI_RETENTION_DAYS=14
NGINX_ACCESS_LOG_RETENTION_DAYS=30
NGINX_ERROR_LOG_RETENTION_DAYS=30
REQUEST_ID_HEADER=X-Request-ID
```

Secrets such as `SENTRY_DSN`, Telegram token, SMTP password, and provider credentials must come from runtime secret storage, not from Git.

## Activation commands

Run on the production host after DNS/TLS is active:

```bash
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime ./infra/deploy/validate-monitoring-live.sh
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime ./infra/deploy/validate-alert-delivery.sh
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime ./infra/deploy/validate-sentry-test-event.sh
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime ./infra/deploy/validate-request-id-live.sh
```

## Evidence

Use:

```text
infra/monitoring/monitoring-apm-logs-evidence-template.md
```

Save filled evidence outside Git or attach it to private release notes.

## Release gate

P3-04 is production-closed only when:

- uptime checks are active;
- at least one alert channel delivers a test notification;
- Sentry test event is visible;
- logs are searchable by request ID;
- retention policy is configured and recorded.

## Secret handling notice

DO NOT commit real Sentry DSNs, Telegram tokens, SMTP passwords, Grafana credentials, Uptime Kuma credentials, Loki credentials, `.env.runtime` files, raw logs containing personal data, or filled monitoring evidence to the repository.
