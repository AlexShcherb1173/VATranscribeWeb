# Centralized logging

VATranscribe production uses structured JSON stdout logs plus Docker `json-file` rotation as the local fallback. Centralized search can be connected through Loki/Promtail/Grafana or a managed provider such as BetterStack, Grafana Cloud, ELK/OpenSearch or Datadog.

Default targets:

- Docker local logs: `max-size=50m`, `max-file=5`
- Loki retention: 14 days
- Nginx access/error logs target: 30 days
- Audit/security DB logs: 180 days

Search keys:

- `request_id`
- `service`
- `container`
- `level`
- `logger`
- `path`
- `status_code`

Run optional local observability overlay on a Linux Docker host. `GRAFANA_ADMIN_PASSWORD` is mandatory and must be supplied through the protected runtime environment; there is no default production password:

```bash
docker compose -f infra/logging/docker-compose.observability.yml up -d
```

This overlay is not a replacement for off-host retention. For production, store logs outside the application host or use a managed logging provider.
