# Stage 4 Production Readiness Backlog

Stage 4 starts after Stage 3 final review.

## Goal

Move VATranscribeWeb from deploy-ready structure to production-ready operation.

## 4.1 Infrastructure

- Configure production domains.
- Configure SSL certificates and auto-renewal.
- Add HTTPS-only deployment.
- Add CDN for static assets.
- Define backup policy for PostgreSQL.
- Implement automatic DB backups.
- Define backup retention.
- Test restore procedure.
- Add uptime monitoring with alerts.
- Add rollback procedure.
- Document production deployment runbook.

## 4.2 Observability

- Add application error monitoring: Sentry, NewRelic or equivalent.
- Add backend structured logging.
- Add Nginx access/error log retention.
- Add centralized log storage/search.
- Add API health dashboards.
- Add worker health/queue monitoring.
- Add alerting rules.

## 4.3 Security

- Move secrets to vault / secret manager.
- Remove development secrets from production env.
- Harden CORS for production domains.
- Add HTTPS/HSTS.
- Review security headers.
- Run OWASP Top-10 checklist.
- Review dependency audit results.
- Add production rate limiting topology.
- Add admin 2FA.
- Review audit log coverage.
- Prepare internal security audit checklist.

## 4.4 SEO / Analytics

- Set production canonical URL.
- Generate production sitemap with production domain.
- Validate robots.txt.
- Validate hreflang.
- Validate schema.org / JSON-LD.
- Add Yandex Metrika, GA or equivalent.
- Add analytics events for CTA, registration, pricing and download.
- Check Core Web Vitals.
- Add production 404 and 500 pages.
- Validate OpenGraph preview.

## 4.5 Legal / Compliance

- Finalize Privacy Policy.
- Finalize Terms of Use.
- Finalize Personal Data Policy.
- Finalize Cookie Policy.
- Finalize Refund Policy.
- Add cookie consent UI.
- Review 152-FZ requirements if processing personal data of Russian users.
- Add business/legal contact data.
- Define data retention policy.
- Define user data deletion/export process.

## 4.6 CI/CD and release

- Complete production deployment workflow.
- Add environment-specific build variables.
- Add migration step policy.
- Add zero-downtime or controlled downtime deployment policy.
- Add release tags.
- Add deployment approvals if needed.
- Add rollback command/runbook.
- Add smoke tests after deployment.

## Stage 4 acceptance criteria

- Production domain works over HTTPS.
- Marketing app and SaaS app are routed correctly.
- API health endpoints are available through production reverse proxy.
- Backups are automatic and restore-tested.
- Logs and errors are observable.
- Secrets are not stored in repository or plain deployment files.
- Analytics and SEO are validated.
- Legal pages and cookie consent are production-ready.
- Rollback procedure is documented and tested.
