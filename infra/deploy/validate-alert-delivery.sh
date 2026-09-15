#!/usr/bin/env bash
set -euo pipefail

# P3-04 alert delivery validation.
# Do not echo tokens, webhooks, SMTP passwords, or recipient secrets.

RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
REQUIRE_ALERT_DELIVERY="${REQUIRE_ALERT_DELIVERY:-true}"
ALERT_TEST_MESSAGE="${ALERT_TEST_MESSAGE:-VATranscribe P3-04 monitoring alert delivery test}"

if [[ -f "${RUNTIME_ENV_FILE}" ]]; then
  set -a
  # shellcheck source=/dev/null
  . "${RUNTIME_ENV_FILE}"
  set +a
fi

sent_any="false"

if [[ -n "${TELEGRAM_ALERT_BOT_TOKEN:-}" && -n "${TELEGRAM_ALERT_CHAT_ID:-}" ]]; then
  echo "[INFO] Sending Telegram alert test"
  curl --fail --silent --show-error --max-time 15 \
    --request POST \
    --data-urlencode "chat_id=${TELEGRAM_ALERT_CHAT_ID}" \
    --data-urlencode "text=${ALERT_TEST_MESSAGE}" \
    "https://api.telegram.org/bot${TELEGRAM_ALERT_BOT_TOKEN}/sendMessage" >/dev/null
  echo "[OK] Telegram alert delivery request accepted"
  sent_any="true"
else
  echo "[INFO] Telegram alert variables are not fully configured"
fi

if [[ -n "${SMTP_HOST:-}" && -n "${SMTP_USERNAME:-}" && -n "${SMTP_PASSWORD:-}" && -n "${ALERT_EMAIL_TO:-}" ]]; then
  echo "[INFO] Sending email alert test"
  python - <<'PY'
import os
import smtplib
from email.message import EmailMessage

host = os.environ["SMTP_HOST"]
port = int(os.environ.get("SMTP_PORT", "587"))
username = os.environ["SMTP_USERNAME"]
password = os.environ["SMTP_PASSWORD"]
recipient = os.environ["ALERT_EMAIL_TO"]
sender = os.environ.get("ALERT_EMAIL_FROM", username)
message_text = os.environ.get("ALERT_TEST_MESSAGE", "VATranscribe P3-04 monitoring alert delivery test")

msg = EmailMessage()
msg["Subject"] = "VATranscribe P3-04 alert delivery test"
msg["From"] = sender
msg["To"] = recipient
msg.set_content(message_text)

with smtplib.SMTP(host, port, timeout=15) as server:
    server.starttls()
    server.login(username, password)
    server.send_message(msg)

print("[OK] Email alert delivery request accepted")
PY
  sent_any="true"
else
  echo "[INFO] Email alert variables are not fully configured"
fi

if [[ "${sent_any}" != "true" && "${REQUIRE_ALERT_DELIVERY}" == "true" ]]; then
  echo "[FAIL] No alert delivery channel was tested" >&2
  echo "[HINT] Configure Telegram or email alert variables in ${RUNTIME_ENV_FILE}" >&2
  exit 1
fi

echo "[OK] P3-04 alert delivery validation completed"
