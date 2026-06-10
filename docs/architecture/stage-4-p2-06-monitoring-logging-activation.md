# Stage 4 / P2-06 — Monitoring/logging activation

## Scope

- Uptime checks for marketing, app, API live and API ready endpoints.
- Alert channel placeholders for Telegram/email.
- Sentry/APM activation for API and worker; frontend bootstrap support.
- Structured JSON logs with request IDs.
- Nginx JSON access logs with request correlation.
- Optional Loki/Promtail/Grafana overlay.
- Production validation gates and docs.

## Status

`P2-06_monitoring_logging_activation: CLOSED` after static tests, full pytest, frontend build and compose config pass.
