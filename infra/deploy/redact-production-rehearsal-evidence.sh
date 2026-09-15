#!/usr/bin/env bash
set -euo pipefail

INPUT_FILE="${1:-}"
OUTPUT_FILE="${2:-}"

if [[ -z "${INPUT_FILE}" || -z "${OUTPUT_FILE}" || ! -f "${INPUT_FILE}" ]]; then
  echo "Usage: $0 <raw-evidence-file> <redacted-evidence-file>" >&2
  exit 2
fi

mkdir -p "$(dirname "${OUTPUT_FILE}")"
cp "${INPUT_FILE}" "${OUTPUT_FILE}"

# DO NOT commit raw production rehearsal evidence. This redactor is a safety net, not a substitute for review.
sed -i -E 's#(postgresql(\+psycopg)?://)[^ @:/]+:[^ @]+@#\1<redacted>:<redacted>@#g' "${OUTPUT_FILE}"
sed -i -E 's#(DATABASE_URL=).*#\1<redacted>#g' "${OUTPUT_FILE}"
sed -i -E 's#(POSTGRES_PASSWORD=).*#\1<redacted>#g' "${OUTPUT_FILE}"
sed -i -E 's#(SECRET_KEY=).*#\1<redacted>#g' "${OUTPUT_FILE}"
sed -i -E 's#(YOUTUBE_COOKIES_ENCRYPTION_KEY=).*#\1<redacted>#g' "${OUTPUT_FILE}"
sed -i -E 's#(PAYMENT_API_KEY=).*#\1<redacted>#g' "${OUTPUT_FILE}"
sed -i -E 's#(PAYMENT_WEBHOOK_SECRET=).*#\1<redacted>#g' "${OUTPUT_FILE}"
sed -i -E 's#(SENTRY_DSN=).*#\1<redacted>#g' "${OUTPUT_FILE}"
sed -i -E 's#(TELEGRAM_ALERT_BOT_TOKEN=).*#\1<redacted>#g' "${OUTPUT_FILE}"
sed -i -E 's#(SMTP_PASSWORD=).*#\1<redacted>#g' "${OUTPUT_FILE}"
sed -i -E 's#(AGE_IDENTITY_FILE=).*#\1<redacted>#g' "${OUTPUT_FILE}"
sed -i -E 's#(/opt/vatranscribe/secrets/)[^ ]+#\1<redacted>#g' "${OUTPUT_FILE}"
sed -i -E 's#(password|secret|token|key)=([^ ]+)#\1=<redacted>#Ig' "${OUTPUT_FILE}"
sed -i -E 's#(Authorization: Bearer )[A-Za-z0-9._~+/=-]+#\1<redacted>#g' "${OUTPUT_FILE}"

chmod 600 "${OUTPUT_FILE}" || true

echo "[OK] Redacted production rehearsal evidence written to ${OUTPUT_FILE}"
echo "[INFO] DO NOT commit raw or redacted live evidence to Git. Store it in the controlled release evidence vault."
