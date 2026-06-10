#!/usr/bin/env bash
set -euo pipefail

# P3-04 Sentry/APM test event validation.
# Do not print SENTRY_DSN or other secrets.

RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-/opt/vatranscribe/secrets/.env.runtime}"
SENTRY_TEST_EVENT_MESSAGE="${SENTRY_TEST_EVENT_MESSAGE:-VATranscribe P3-04 Sentry test event}"

if [[ -f "${RUNTIME_ENV_FILE}" ]]; then
  set -a
  # shellcheck source=/dev/null
  . "${RUNTIME_ENV_FILE}"
  set +a
fi

python - <<'PY'
from __future__ import annotations

import os
import sys
import uuid

PLACEHOLDERS = {"", "changeme", "change_me", "placeholder", "example", "local-dev"}

def looks_like_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    normalized = value.strip().lower()
    return normalized in PLACEHOLDERS or "change_me" in normalized or "example.com" in normalized

if looks_like_placeholder(os.environ.get("SENTRY_DSN")):
    print("[FAIL] SENTRY_DSN is not configured or still looks like a placeholder", file=sys.stderr)
    sys.exit(1)

try:
    import sentry_sdk
except Exception as exc:
    print(f"[FAIL] sentry_sdk import failed: {exc}", file=sys.stderr)
    sys.exit(1)

release = os.environ.get("RELEASE_VERSION") or os.environ.get("GITHUB_SHA") or "manual-p3-04"
environment = os.environ.get("SENTRY_ENVIRONMENT") or os.environ.get("APP_ENV") or "production"
message = os.environ.get("SENTRY_TEST_EVENT_MESSAGE", "VATranscribe P3-04 Sentry test event")
marker = uuid.uuid4().hex

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    environment=environment,
    traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
    profiles_sample_rate=float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.0")),
    release=release,
    send_default_pii=False,
)

event_id = sentry_sdk.capture_message(f"{message} marker={marker}", level="warning")
sentry_sdk.flush(timeout=10)

print(f"[OK] SENTRY_TEST_EVENT_ID={event_id}")
print(f"[OK] SENTRY_TEST_EVENT_MARKER={marker}")
print(f"[INFO] SENTRY_ENVIRONMENT={environment}")
print(f"[INFO] RELEASE_VERSION={release}")
PY
