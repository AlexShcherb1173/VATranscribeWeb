# Sentry test event

Runtime env path: `/opt/vatranscribe/secrets/.env.runtime`.

P3-04 requires a visible Sentry/APM test event before production release.

Expected runtime variables:

```env
APM_PROVIDER=sentry
SENTRY_REQUIRED=true
SENTRY_DSN=<from runtime secret storage>
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.05
SENTRY_PROFILES_SAMPLE_RATE=0.0
RELEASE_VERSION=<git sha or release tag>
```

Run:

```bash
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime ./infra/deploy/validate-sentry-test-event.sh
```

Expected sanitized output:

```text
[OK] SENTRY_TEST_EVENT_ID=<event id>
[OK] SENTRY_TEST_EVENT_MARKER=<marker>
[INFO] SENTRY_ENVIRONMENT=production
[INFO] RELEASE_VERSION=<release>
```

Confirm that the event is visible in Sentry for the production environment and current release.

## Secret handling notice

DO NOT commit `SENTRY_DSN`, Sentry auth tokens, screenshots containing tokens, or filled Sentry evidence to the repository.
