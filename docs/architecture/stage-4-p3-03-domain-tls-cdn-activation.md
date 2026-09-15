# Stage 4 / P3-03 Domain / TLS / CDN activation

## Status

Foundation target: add live validation scripts, checklists, and evidence templates for DNS, TLS, Certbot renewal, HSTS, and CDN cache behavior.

Production target: run these checks against the real production domains and store redacted evidence outside Git.

DO NOT commit DNS/CDN tokens, TLS private keys, Certbot account keys, SSH keys, server passwords, or live evidence that exposes secrets.

Runtime env source: `/opt/vatranscribe/secrets/.env.runtime`

## Scope

- `vatranscribe.ru` for marketing/root.
- `app.vatranscribe.ru` for the user app.
- `api.vatranscribe.ru` for backend API.
- `admin.vatranscribe.ru` for admin panel.
- HTTP-01 Certbot challenge through nginx webroot.
- HSTS enabled, preload disabled until all subdomains are stable.
- CDN for marketing/app static assets only.
- API excluded from CDN caching.

## Added controls

- `infra/deploy/validate-dns-live.sh` validates DNS records and optional expected IP.
- `infra/deploy/validate-tls-hsts-live.sh` validates TLS expiry, HSTS, and HTTP-to-HTTPS redirect.
- `infra/deploy/validate-cdn-cache-live.sh` validates HTML/API/static cache policies.
- `infra/deploy/domain-tls-cdn-activation-checklist.md` defines operational close criteria.
- `infra/deploy/domain-tls-cdn-evidence-template.md` defines sanitized release evidence.
- `docs/deployment/domain-tls-cdn-activation.md` defines production activation sequence.

## Production close criteria

P3-03 is production-closed only when live DNS, CDN, Certbot issue, renewal dry-run, TLS, and HSTS evidence exist for the real production domains.

## Remaining after foundation

- Choose real DNS/CDN providers.
- Set `PRODUCTION_HOST_PUBLIC_IP`.
- Replace `CERTBOT_EMAIL=admin@example.com` with real ops email.
- Run live Certbot issue and dry-run.
- Verify CDN cache HIT/MISS behavior with real hashed asset URLs.
