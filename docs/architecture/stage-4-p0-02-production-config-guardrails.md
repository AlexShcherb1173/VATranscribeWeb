# Stage 4 / P0-02 — Production config guardrails

## Status

`P0-02_production_config_guardrails` closes the second production-readiness blocker after private storage access.

The application must not start in `APP_ENV=production` with unsafe defaults.

## Implemented controls

### Environment mode

Allowed values:

- `development`
- `test`
- `production`

Any other value is rejected by settings validation.

### Debug mode

Production requires:

```env
APP_ENV=production
DEBUG=false
```

`APP_ENV=production` with `DEBUG=true` is rejected at settings startup.

### API docs / OpenAPI

Production requires:

```env
EXPOSE_API_DOCS=false
```

FastAPI docs are now controlled by settings:

- `docs_url=settings.docs_url`
- `redoc_url=settings.redoc_url`
- `openapi_url=settings.openapi_url`

When API docs are disabled, `/docs`, `/redoc`, and `/openapi.json` are not publicly exposed by FastAPI.

### Secret key

Production rejects:

- missing or short `SECRET_KEY` values;
- default/change-me values;
- obvious development secrets.

Minimum production length: 32 characters.

### CORS

Production requires explicit HTTPS origins.

Rejected in production:

- `*`
- empty `CORS_ORIGINS`
- `localhost`
- `127.0.0.1`
- `0.0.0.0`
- `http://` origins

Expected production shape:

```env
CORS_ORIGINS=https://vatranscribe.ru,https://app.vatranscribe.ru,https://admin.vatranscribe.ru
```

### Public domains

Production requires these origins to be explicit and HTTPS-only:

```env
PUBLIC_MARKETING_ORIGIN=https://vatranscribe.ru
PUBLIC_APP_ORIGIN=https://app.vatranscribe.ru
PUBLIC_API_ORIGIN=https://api.vatranscribe.ru
PUBLIC_ADMIN_ORIGIN=https://admin.vatranscribe.ru
```

These values are separated from frontend build variables so the backend can validate its own production perimeter.

### JWT policy

Production guardrails:

```env
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
```

Allowed algorithms:

- `HS256`
- `RS256`

The JWT encode/decode path now reads the algorithm from settings instead of using a hardcoded module constant.

### Cookie policy

Production requires:

```env
COOKIE_SECURE=true
COOKIE_HTTPONLY=true
COOKIE_SAMESITE=lax
COOKIE_DOMAIN=.vatranscribe.ru
```

Allowed `COOKIE_SAMESITE` values:

- `lax`
- `strict`

`COOKIE_DOMAIN` is allowed to be empty in development/test, but is mandatory in production.

## Files changed

- `apps/api/app/config.py`
- `apps/api/app/main.py`
- `apps/api/app/security.py`
- `apps/api/app/schemas.py`
- `.env.example`
- `.env.production.example`
- `tests/security/test_production_config_guardrails_static.py`
- `docs/architecture/stage-4-p0-02-production-config-guardrails.md`

## Verification

Run:

```powershell
pytest tests/security/test_production_config_guardrails_static.py -v
pytest -v
npm --prefix apps/web run build
```

Also verify the docs strings are no longer hardcoded:

```powershell
Select-String -Path .\apps\api\app\main.py -Pattern "docs_url='/docs'|redoc_url='/redoc'|openapi_url='/openapi.json'"
```

Expected result: no output.

## Remaining Stage 4 work

This patch is configuration hardening only. It does not yet implement:

- HttpOnly refresh-token cookies in the auth router;
- CSRF protection for cookie-based auth;
- Redis-backed distributed rate limiting;
- production Nginx TLS/HSTS/CSP headers;
- vault/secret manager integration.

Those are separate Stage 4 tasks.
