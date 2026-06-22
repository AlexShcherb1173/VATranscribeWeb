# P3-08 Production rehearsal checklist

This checklist is for the final staging/production rehearsal before public release.

DO NOT store real secrets, `.env.runtime`, SSH keys, payment keys, Sentry DSNs, Telegram tokens, SMTP passwords, backup files, raw logs, or raw evidence in Git.

## Required context

- Runtime env file: `/opt/vatranscribe/secrets/.env.runtime`.
- Project path: `/opt/vatranscribe/app` or documented staging equivalent.
- Evidence path: `/opt/vatranscribe/release-evidence/production-rehearsal` or controlled evidence vault.
- Release candidate commit is recorded.
- Rollback reference is recorded before deploy.

## Rehearsal gates

- [ ] Staging deploy executed from the release candidate.
- [ ] Runtime secrets validation passed.
- [ ] Docker Compose production config rendered with runtime env.
- [ ] Migrations completed with `python -m alembic upgrade head`.
- [ ] Smoke checks passed for `/api/v1/health/live` and `/api/v1/health/ready`.
- [ ] Rollback was executed and measured.
- [ ] Rollback duration was less than or equal to 300 seconds.
- [ ] Backup/restore proof was executed or referenced with current release evidence.
- [ ] Auth checks passed.
- [ ] Files/private storage checks passed.
- [ ] Jobs/worker checks passed.
- [ ] Billing checks passed: fake upgrades disabled, paid activation requires webhook/provider evidence.
- [ ] Cookie consent checks passed.
- [ ] Analytics checks passed: analytics is consent-gated and test event is verified.
- [ ] Monitoring/APM/logs checks passed, including request_id search evidence.
- [ ] Supply-chain evidence and High/Critical triage are complete.
- [ ] Legal/152-ФЗ final review is complete or explicitly blocks public launch.

## GO / NO-GO rule

Public production launch is NO-GO if any of these are missing:

- real runtime secrets outside Git;
- DNS/TLS/CDN evidence;
- monitoring/APM/logging evidence;
- encrypted backup and restore drill evidence;
- supply-chain evidence and High/Critical triage;
- legal/152-ФЗ final review;
- rollback timing proof within 5 minutes;
- smoke and functional checks for auth/files/jobs/billing/cookie/analytics.
