# Monitoring release checklist

Set `MONITORING_RELEASE_CHECKLIST_ACK=true` only after all items below are done on the production host.

- [ ] Uptime checks exist for marketing, app, API live and API ready endpoints.
- [ ] At least one alert channel is enabled and tested.
- [ ] `SENTRY_DSN` is configured when `SENTRY_REQUIRED=true`.
- [ ] Backend test event is visible in Sentry/APM.
- [ ] Worker test event is visible in Sentry/APM.
- [ ] Frontend error capture path is configured or documented.
- [ ] Central log collector is running or provider is connected.
- [ ] Logs are searchable by `request_id`, `container`, `service`, `level`.
- [ ] Retention is configured: Loki 14 days, access/error logs 30 days, audit logs 180 days.
- [ ] On-call/runbook owner is known.
