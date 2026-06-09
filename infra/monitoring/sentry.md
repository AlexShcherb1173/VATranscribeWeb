# Sentry/APM

Production `.env`:

```env
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
SENTRY_TRACES_SAMPLE_RATE=0.05
RELEASE_VERSION=vatranscribe-web-<git-sha-or-tag>
LOG_JSON=true
LOG_LEVEL=INFO
```

Rules: `send_default_pii=false`, low trace sampling, no secrets/cookies/raw media metadata in events.
