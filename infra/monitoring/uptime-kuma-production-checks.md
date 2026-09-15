# Uptime Kuma production checks

Runtime env path: `/opt/vatranscribe/secrets/.env.runtime`.

Create these checks in Uptime Kuma or in an external uptime provider.

| Monitor | URL | Interval | Retry | Expected | Alert channels |
|---|---|---:|---:|---|---|
| VATranscribe marketing | `https://vatranscribe.ru/` | 60s | 3 | 200/3xx | Telegram, email |
| VATranscribe app | `https://app.vatranscribe.ru/app/` | 60s | 3 | 200/3xx | Telegram, email |
| VATranscribe API live | `https://api.vatranscribe.ru/api/v1/health/live` | 30s | 3 | 200 | Telegram, email |
| VATranscribe API ready | `https://api.vatranscribe.ru/api/v1/health/ready` | 60s | 3 | 200 | Telegram, email |
| VATranscribe admin | `https://admin.vatranscribe.ru/` | 60s | 3 | 200/3xx | Telegram, email |

`/health/ready` is the primary dependency check because it should fail when DB, Redis, or storage dependencies are unavailable.

Run the live validator after DNS/TLS is active:

```bash
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime ./infra/deploy/validate-monitoring-live.sh
```

## Secret handling notice

DO NOT commit Uptime Kuma credentials, alert tokens, private monitor export files, or filled production evidence to the repository.
