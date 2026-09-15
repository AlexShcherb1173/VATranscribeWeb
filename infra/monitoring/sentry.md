# Sentry/APM activation

Production uses provider-neutral env variables and Sentry as the default APM provider.

Required production variables when Sentry is enabled:

```env
APM_PROVIDER=sentry
SENTRY_REQUIRED=true
SENTRY_DSN=<from vault/runtime env>
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.05
SENTRY_PROFILES_SAMPLE_RATE=0.0
SENTRY_WORKER_ENABLED=true
VITE_SENTRY_DSN=<frontend DSN if browser tracking is enabled>
VITE_SENTRY_ENVIRONMENT=production
VITE_SENTRY_RELEASE=<git sha or release tag>
```

The API initializes Sentry with FastAPI, SQLAlchemy and logging integrations.
The worker initializes Sentry with Celery, SQLAlchemy and logging integrations.
The frontend includes environment-driven bootstrap support; load the Sentry browser SDK or replace the bootstrap with `@sentry/react` when final frontend telemetry policy is approved.

Do not enable analytics/error tracking cookies before the cookie consent model is finalized.
