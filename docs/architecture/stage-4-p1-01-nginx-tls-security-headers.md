# Stage 4 — P1-01 Nginx TLS and Security Headers

## Status

`P1-01_nginx_tls_security_headers` adds a production-ready Nginx security baseline.

This patch is intentionally split into two configs:

- `infra/docker/nginx.conf` — local/development HTTP config with security headers, body limits and rate-limit zones.
- `infra/docker/nginx.prod.conf.template` — production HTTPS template rendered by the official Nginx Docker entrypoint via environment variables.

## Scope

Implemented:

- HTTPS-ready production Nginx template.
- HTTP -> HTTPS redirect.
- Let's Encrypt webroot challenge path.
- HSTS without `preload`.
- CSP baseline.
- `X-Content-Type-Options`.
- `Referrer-Policy`.
- `Permissions-Policy`.
- `X-Frame-Options DENY` plus CSP `frame-ancestors 'none'`.
- Split request body limits.
- Nginx `limit_req_zone` for auth, strict auth, upload, download and general API surfaces.
- Static tests for TLS/security-header config.

## Production variables

Defined in `.env.production.example`:

```env
NGINX_SERVER_NAME=vatranscribe.ru app.vatranscribe.ru api.vatranscribe.ru admin.vatranscribe.ru
NGINX_SSL_CERTIFICATE=/etc/letsencrypt/live/vatranscribe.ru/fullchain.pem
NGINX_SSL_CERTIFICATE_KEY=/etc/letsencrypt/live/vatranscribe.ru/privkey.pem
NGINX_HSTS_MAX_AGE=31536000
NGINX_GENERAL_API_RATE=120r/m
NGINX_AUTH_RATE=10r/m
NGINX_AUTH_STRICT_RATE=5r/m
NGINX_UPLOAD_RATE=10r/m
NGINX_DOWNLOAD_RATE=30r/m
NGINX_GLOBAL_BODY_LIMIT=20m
NGINX_AUTH_BODY_LIMIT=1m
NGINX_ANALYZE_BODY_LIMIT=2m
NGINX_UPLOAD_BODY_LIMIT=1024m
WEB_HTTPS_PORT=443
```

## Request body limits

| Surface | Limit |
|---|---:|
| Global API | 20m |
| Auth | 1m |
| URL analyze | 2m |
| Uploads | 1024m |

## Rate limits

| Surface | Rate |
|---|---:|
| General API | 120r/m |
| Auth | 10r/m |
| Login/register | 5r/m |
| Uploads | 10r/m |
| Downloads/exports | 30r/m |

## CSP baseline

Production template:

```text
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';
img-src 'self' data: blob:;
font-src 'self' data:;
connect-src 'self' ${PUBLIC_API_ORIGIN};
frame-ancestors 'none';
base-uri 'self';
form-action 'self'
```

`style-src 'unsafe-inline'` is kept temporarily for frontend compatibility. It should be revisited after checking generated CSS and runtime inline styles.

## HSTS

```text
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

`preload` is intentionally not enabled until all subdomains are verified as HTTPS-only.

## Follow-up

- Add certbot/ACME automation or cloud certificate provisioning.
- Add production smoke test for HTTP -> HTTPS redirect.
- Add runtime header checks against deployed environment.
- Revisit CSP after choosing analytics, Sentry/PostHog, payments and external media sources.
