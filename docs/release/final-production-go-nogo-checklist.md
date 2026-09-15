# Final production GO / NO-GO checklist

This checklist is the final release decision record for VATranscribeWeb.

DO NOT commit completed evidence, secrets, raw logs, backup files, scanner outputs, or private legal/operator details to Git.

## Hard NO-GO blockers

Public production launch is NO-GO if any item below is incomplete:

- [ ] Runtime secrets are configured outside Git at `/opt/vatranscribe/secrets/.env.runtime`.
- [ ] Production config has `APP_ENV=production` and `DEBUG=false`.
- [ ] Default development secrets are absent from live compose output.
- [ ] DNS, TLS, Certbot renewal dry-run, HSTS, and CDN cache evidence exists.
- [ ] Uptime checks and Telegram/email alerts are verified.
- [ ] Sentry/APM test event is visible.
- [ ] Centralized logs are searchable by `request_id` / `X-Request-ID`.
- [ ] Encrypted backup exists with manifest and SHA-256 checksum.
- [ ] Restore drill into disposable DB passed.
- [ ] Supply-chain evidence exists: pip-audit, npm audit, Trivy, Gitleaks, Syft SBOM.
- [ ] High/Critical vulnerability triage is complete.
- [ ] Legal/152-ФЗ final review is complete.
- [ ] Staging deploy rehearsal passed.
- [ ] Alembic migrations completed successfully.
- [ ] Smoke checks passed.
- [ ] Rollback completed in 300 seconds or less.
- [ ] Auth checks passed.
- [ ] Private files/storage checks passed.
- [ ] Jobs/worker checks passed.
- [ ] Billing checks passed and fake paid-plan upgrade is disabled.
- [ ] Cookie consent checks passed.
- [ ] Analytics checks passed and analytics is consent-gated.

## Decision

- Release candidate commit:
- Release owner:
- Decision: GO / NO-GO
- Decision time UTC:
- Evidence vault path:
- Remaining accepted risks:

## Post-launch watch

- Monitor uptime and alerts during the first 24 hours.
- Watch Sentry issue stream and request rate anomalies.
- Verify backup job after first scheduled run.
- Verify analytics events only after consent.
