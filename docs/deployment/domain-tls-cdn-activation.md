# Domain / TLS / CDN activation

P3-03 activates the domain, TLS, Certbot, HSTS, and CDN production path for VATranscribeWeb.

DO NOT commit DNS/CDN API tokens, TLS private keys, ACME account keys, SSH keys, server passwords, or unsanitized live evidence.

Runtime env source: `/opt/vatranscribe/secrets/.env.runtime`

## Defaults accepted for P3-03

| Setting | Value |
|---|---|
| Production public IP | not set yet |
| DNS provider | manual DNS for now |
| CDN provider | provider-neutral for now |
| Certbot email | `admin@example.com` placeholder until real ops email is set |
| Certbot challenge | HTTP-01 via nginx webroot |
| Wildcard certificate | no |
| HSTS preload | no for now |
| CDN for API | no |
| CDN for marketing/static | yes |
| CDN for app static | yes |
| CDN cache HTML | no-cache or short TTL |
| CDN cache assets | long TTL |

## Runtime variables to finalize

The following values must be configured in `/opt/vatranscribe/secrets/.env.runtime` before production close:

```env
ROOT_DOMAIN=vatranscribe.ru
MARKETING_DOMAIN=vatranscribe.ru
APP_DOMAIN=app.vatranscribe.ru
API_DOMAIN=api.vatranscribe.ru
ADMIN_DOMAIN=admin.vatranscribe.ru
PRODUCTION_HOST_PUBLIC_IP=<real-public-ip>
DNS_PROVIDER=<provider-name>
CDN_PROVIDER=<provider-name-or-provider-neutral>
CERTBOT_EMAIL=<real-ops-email>
CERTBOT_DOMAINS=vatranscribe.ru,app.vatranscribe.ru,api.vatranscribe.ru,admin.vatranscribe.ru
CERTBOT_PRIMARY_DOMAIN=vatranscribe.ru
CERTBOT_STAGING=false
CHECK_DNS_EXPECTED_IP=true
NGINX_HSTS_MAX_AGE=31536000
HSTS_PRELOAD_ENABLED=false
CDN_API_ENABLED=false
CDN_MARKETING_STATIC_ENABLED=true
CDN_APP_STATIC_ENABLED=true
CDN_HTML_CACHE_POLICY=no-cache
CDN_ASSET_CACHE_SECONDS=31536000
CDN_STATIC_TEST_URLS=https://vatranscribe.ru/<hashed-asset>,https://app.vatranscribe.ru/<hashed-asset>
```

## Activation sequence

1. Configure DNS A/AAAA/CNAME/CAA records.
2. Verify DNS propagation.
3. Start production nginx with HTTP-01 webroot enabled.
4. Issue live certificate with Certbot.
5. Run renewal dry-run.
6. Verify TLS, HTTP-to-HTTPS redirect, and HSTS.
7. Configure CDN cache rules.
8. Verify HTML/API no-cache and static asset long-cache behavior.
9. Save redacted evidence outside Git.

## Commands

```bash
cd /opt/vatranscribe/app
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime infra/deploy/validate-dns-live.sh
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime infra/deploy/certbot-issue.sh
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime infra/deploy/certbot-renew-dry-run.sh
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime infra/deploy/validate-tls-hsts-live.sh
RUNTIME_ENV_FILE=/opt/vatranscribe/secrets/.env.runtime infra/deploy/validate-cdn-cache-live.sh
```

## Cache policy

| Traffic | CDN | Required policy |
|---|---:|---|
| API | no | `no-store` / `no-cache`, no CDN caching |
| HTML | optional | `no-cache`, short TTL, revalidation |
| Hashed static assets | yes | `public, max-age=31536000, immutable` |
| ACME challenge | no | reachable over HTTP, no-store acceptable |

## Production close criteria

- DNS resolves correctly for all domains.
- Live Let's Encrypt certificate is issued.
- Renewal dry-run passes.
- HSTS header is live.
- API is not cached.
- Static assets are cacheable through CDN.
- Evidence is sanitized and retained outside the repository.
