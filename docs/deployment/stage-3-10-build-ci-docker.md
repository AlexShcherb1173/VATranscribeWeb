# Stage 3.10 Build / CI / Docker / Nginx / Deploy-ready Structure

Stage 3.10 adds a production-like static frontend container and CI checks.

## Local build checks

```powershell
npm run build:marketing
npm run build:web
docker compose exec api python -m pytest tests/security tests/privacy

Production-like compose check
docker compose -f docker-compose.yml -f infra/compose/docker-compose.prod.yml config
Production-like web build
docker compose -f docker-compose.yml -f infra/compose/docker-compose.prod.yml build web
Production-like route check
docker compose -f docker-compose.yml -f infra/compose/docker-compose.prod.yml up -d api web

Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080/healthz"
Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080/"
Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080/pricing"
Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080/auth/login"
Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080/app/"
Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080/api/v1/health/live"
Route strategy

Nginx serves:

RouteTarget
/Astro marketing static app
/pricing, /download, /blog, /resources, /docs, /changelogAstro marketing
/ru/*Astro marketing localized pages
/auth/*React SaaS app
/app/*React SaaS app
/dashboard, /billingReact SaaS app compatibility routes
/api/*FastAPI service
/storage/*FastAPI storage mount
CI

Current workflows:

.github/workflows/web-ci.yml
.github/workflows/backend-ci.yml
.github/workflows/desktop-ci.yml
.github/workflows/release.yml

Stage 3.10 provides CI validation, not full production release automation.

Stage 4 boundary

The following remain Stage 4 Production Readiness tasks:

SSL and HSTS
CDN
production secrets vault
backup and restore testing
APM and centralized logs
production rollback
external uptime monitoring
analytics and pixels
final legal review

## Rollup optional dependency note

The production-like frontend Docker build uses:

```text
npm install --include=optional --no-audit --no-fund
This avoids the Rollup native optional dependency issue that can appear when a lockfile generated on Windows is installed inside a Linux container.

The failure usually looks like:

Cannot find module @rollup/rollup-linux-x64-musl

This is a build environment compatibility fix, not an application runtime change.\n\n## Alpine Rollup native package fix

The production-like frontend Docker image uses `node:22-alpine`, so Rollup needs the musl native package:

```text
@rollup/rollup-linux-x64-musl
The Dockerfile installs this package explicitly using the Rollup version already installed in node_modules.

This avoids build failures like:

Cannot find module @rollup/rollup-linux-x64-musl

