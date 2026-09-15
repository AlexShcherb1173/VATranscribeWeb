# Stage 4 / P2-05 — CDN, domain and Certbot renewal activation

Status: patch foundation.

## Scope

- Domain variables and DNS readiness checks.
- HTTP-01 Certbot issue/renew/dry-run scripts.
- Systemd timer template for automatic renewal.
- Nginx ACME challenge route.
- CDN cache policy for API, HTML and hashed assets.
- Tests and deployment documentation.

## Security posture

- API CDN cache is disabled by default.
- API responses receive `Cache-Control: no-store`.
- HTML/SPAs use no-cache/revalidate.
- Hashed assets use long TTL immutable cache.
- HSTS is enabled but preload is disabled until all subdomains and rollback are tested.

## Operational evidence required later

- DNS check output.
- Certbot issue output.
- Certbot renewal dry-run output.
- TLS expiry check output.
- CDN cache verification output.
