# Alert delivery check

Runtime env path: `/opt/vatranscribe/secrets/.env.runtime`.

P3-04 requires at least one real alert delivery path before production release.

## Telegram

Expected runtime variables on the production host:

```env
TELEGRAM_ALERT_BOT_TOKEN=<from runtime secret storage>
TELEGRAM_ALERT_CHAT_ID=<from runtime secret storage>
```

Run:

```bash
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime ./infra/deploy/validate-alert-delivery.sh
```

## Email

Expected runtime variables on the production host:

```env
SMTP_HOST=<smtp host>
SMTP_PORT=587
SMTP_USERNAME=<from runtime secret storage>
SMTP_PASSWORD=<from runtime secret storage>
ALERT_EMAIL_FROM=<alerts sender>
ALERT_EMAIL_TO=<ops recipient>
```

The validator supports SMTP over STARTTLS.

## Evidence

Copy only sanitized success lines into `infra/monitoring/monitoring-apm-logs-evidence-template.md`.

## Secret handling notice

DO NOT commit Telegram bot tokens, chat IDs, SMTP passwords, alert recipient exports, or filled alert evidence to the repository.
