# Monitoring and logging activation

P2-06 establishes production monitoring activation for VATranscribe.

## Required production decisions

- Uptime provider: Uptime Kuma template plus external uptime checklist.
- Alert channels: Telegram/email placeholders, real secrets injected through runtime env/vault.
- APM: Sentry.
- Central logs: optional Loki/Promtail/Grafana overlay or managed provider.
- Retention: app/nginx logs 30 days target, Loki 14 days, audit logs 180 days.

## Release gate

Production must set:

```env
MONITORING_REQUIRED=true
MONITORING_RELEASE_CHECKLIST_ACK=true
UPTIME_PROVIDER=uptime-kuma
UPTIME_ALERT_CHANNELS=telegram,email
APM_PROVIDER=sentry
SENTRY_REQUIRED=true
CENTRAL_LOGGING_REQUIRED=true
CENTRAL_LOGGING_PROVIDER=loki
```

`MONITORING_RELEASE_CHECKLIST_ACK=true` is allowed only after `infra/monitoring/monitoring-release-checklist.md` is complete.

## Smoke checks

```bash
./infra/deploy/smoke-test.sh
./infra/deploy/monitoring-smoke.sh
```

## Search flow

1. Use Uptime Kuma to identify failing endpoint.
2. Use API readiness response for dependency status.
3. Search central logs by `request_id`.
4. Check Sentry release/environment for new errors.
5. Roll back if deployment-related.
