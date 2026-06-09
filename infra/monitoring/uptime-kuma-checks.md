# Uptime monitoring checks

Recommended Uptime Kuma/external monitors:

| Name | URL | Interval | Expected |
|---|---|---:|---|
| VATranscribe Web | `https://vatranscribe.ru/healthz` | 60s | 200 |
| VATranscribe API live | `https://api.vatranscribe.ru/api/v1/health/live` | 60s | 200 |
| VATranscribe API ready | `https://api.vatranscribe.ru/api/v1/health/ready` | 60s | 200 |

Alert on `/health/ready` because it validates DB, Redis and storage dependencies.
