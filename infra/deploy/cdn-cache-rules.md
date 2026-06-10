# CDN cache rules

Provider-neutral baseline for VATranscribe.

## Do not cache

| Path | Cache policy | Reason |
|---|---|---|
| `/api/*` | `no-store`, bypass CDN cache | Authenticated and user-specific API |
| `/auth/*`, `/dashboard/*`, `/billing/*`, `/app/*` HTML fallback | no-cache / revalidate | SPA shell can change between releases |
| `/.well-known/acme-challenge/*` | no-store | ACME challenge freshness |

## Cache aggressively

| Path | Cache policy | Reason |
|---|---|---|
| `/assets/*` | `public, max-age=31536000, immutable` | Hashed static assets |
| `/_astro/*` | `public, max-age=31536000, immutable` | Astro hashed assets |
| `/app/assets/*` | `public, max-age=31536000, immutable` | Vite hashed assets |

## CDN provider settings

- Preserve `Host`, `X-Forwarded-Proto`, and client IP headers.
- Do not cache responses with `Set-Cookie`.
- Do not cache authenticated routes.
- Do not enable CDN for `api.vatranscribe.ru` unless cache bypass rules are verified.
- Keep HSTS preload disabled until all subdomains are stable and rollback is tested.
