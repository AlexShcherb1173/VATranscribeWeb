# Stage 4 P0-03 — Auth token storage hardening

## Status

P0-03 moves the auth flow from browser-persisted tokens toward a production-safe split model:

- access token: short-lived and stored only in frontend memory;
- refresh token: stored in a backend-managed HttpOnly Secure SameSite cookie;
- refresh token persistence: DB-backed hashed refresh-token rows with rotation and revoke;
- CSRF: double-submit token required for cookie-based refresh/logout endpoints;
- logout: backend revoke + cookie deletion + frontend memory cleanup;
- CSP: temporary Nginx baseline for XSS blast-radius reduction.

## Cookie model

| Cookie | HttpOnly | Purpose |
|---|---:|---|
| `vatranscribe_refresh_token` | yes | Auth refresh token, sent only to `/api/v1/auth/*`. |
| `vatranscribe_csrf_token` | no | Double-submit CSRF token readable by frontend and sent as `X-CSRF-Token`. |

In production both cookies must use:

```env
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
COOKIE_DOMAIN=.vatranscribe.ru
```

## Request model

| Endpoint | Auth material | CSRF required |
|---|---|---:|
| `POST /auth/login` | password credentials | no |
| `POST /auth/refresh` | refresh cookie | yes |
| `POST /auth/logout` | refresh cookie if present | yes |
| `GET /auth/me` | bearer access token | no |

## Frontend model

- `localStorage` is no longer used for access tokens.
- Access token lives only in module-level memory.
- Axios sends `withCredentials: true`.
- Axios attaches `X-CSRF-Token` for unsafe methods when the CSRF cookie exists.
- On 401, the API client attempts one refresh via the HttpOnly cookie, then retries the original request.

## Remaining follow-up tasks

Runtime/e2e tests still need to cover:

1. login sets refresh + CSRF cookies;
2. hard reload refreshes access token from cookie;
3. logout revokes DB refresh row and clears cookies;
4. old refresh token cannot be reused after rotation;
5. missing/invalid CSRF fails refresh/logout with 403;
6. CSP does not break marketing/app pages after analytics/Sentry are added.
