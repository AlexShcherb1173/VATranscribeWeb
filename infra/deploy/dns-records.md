# VATranscribe DNS records

P2-05 default domain plan:

| Host | Type | Value | Notes |
|---|---|---|---|
| `vatranscribe.ru` | A/AAAA | `PRODUCTION_HOST_PUBLIC_IP` or CDN target | Marketing/root |
| `app.vatranscribe.ru` | A/AAAA | `PRODUCTION_HOST_PUBLIC_IP` or CDN target | Web application |
| `api.vatranscribe.ru` | A/AAAA | `PRODUCTION_HOST_PUBLIC_IP` | API must not be cached by CDN |
| `admin.vatranscribe.ru` | A/AAAA | `PRODUCTION_HOST_PUBLIC_IP` | Admin surface |

Rules:

- API traffic must bypass CDN cache.
- Do not enable wildcard DNS until a wildcard TLS strategy is approved.
- Keep port 80 open for HTTP-01 ACME challenge and HTTP-to-HTTPS redirect.
- Run `infra/deploy/check-domain-readiness.sh` after DNS propagation.
