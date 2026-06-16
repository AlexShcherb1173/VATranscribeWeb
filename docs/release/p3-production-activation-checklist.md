# P3 Production activation checklist

## P3-01 Release hygiene

- [x] `.gitattributes` exists.
- [x] Shell scripts use LF.
- [x] Repository is clean before activation work.

## P3-02 Runtime secrets / vault activation

- [ ] Runtime env file exists at `/opt/vatranscribe/secrets/.env.runtime`.
- [ ] Runtime env file is outside Git.
- [ ] Runtime env permissions are `600` or stricter.
- [ ] `infra/deploy/validate-runtime-env-live.sh` passes on the production host.
- [ ] Redacted runtime evidence has `PLACEHOLDER_COUNT=0`.
- [ ] GitHub Environment `production` exists.
- [ ] Required GitHub deployment secrets are configured.
- [ ] Rotation owner and next rotation date are recorded.

## P3-03 Domain / TLS / CDN activation

- [ ] Runtime env file `/opt/vatranscribe/secrets/.env.runtime` contains final domain/TLS/CDN values.
- [ ] DNS A/AAAA/CNAME records are configured.
- [ ] CAA policy is documented.
- [ ] `infra/deploy/validate-dns-live.sh` passes.
- [ ] Live Certbot issue is completed with HTTP-01 nginx webroot.
- [ ] `infra/deploy/certbot-renew-dry-run.sh` passes.
- [ ] `infra/deploy/validate-tls-hsts-live.sh` confirms TLS, redirect, and HSTS.
- [ ] CDN provider and cache rules are documented.
- [ ] API traffic is not cached by CDN.
- [ ] HTML is no-cache or short TTL.
- [ ] Static hashed assets are long TTL and immutable.
- [ ] `infra/deploy/validate-cdn-cache-live.sh` passes with real `CDN_STATIC_TEST_URLS`.
- [ ] Redacted DNS/TLS/CDN evidence is stored outside Git.

## P3-04 Monitoring / APM / logs activation

- [ ] Runtime env file `/opt/vatranscribe/secrets/.env.runtime` contains final monitoring/APM/logging values.
- [ ] Uptime checks exist for marketing, app, API live, API ready, and admin if public.
- [ ] `infra/deploy/validate-monitoring-live.sh` passes on the production host.
- [ ] Telegram or email alert delivery is verified.
- [ ] `infra/deploy/validate-alert-delivery.sh` passes on the production host.
- [ ] `APM_PROVIDER=sentry` and `SENTRY_REQUIRED=true` are configured.
- [ ] `infra/deploy/validate-sentry-test-event.sh` creates a visible Sentry event.
- [ ] Central logging provider is selected and active: Loki/Grafana or external provider.
- [ ] `infra/deploy/validate-request-id-live.sh` confirms `X-Request-ID` propagation.
- [ ] A generated request ID is found in centralized logs.
- [ ] Retention is configured: Loki 14 days, Nginx access/error logs 30 days, audit logs 180 days.
- [ ] Sanitized `monitoring-apm-logs-evidence` is stored outside Git.

## P3-05 Backup restore proof

- [ ] Runtime env file `/opt/vatranscribe/secrets/.env.runtime` contains final backup/restore values.
- [ ] `BACKUP_DIR=/opt/vatranscribe/backups` is configured on the production host.
- [ ] `BACKUP_REQUIRE_ENCRYPTION=true` is configured.
- [ ] `BACKUP_ENCRYPTION_RECIPIENT` or `AGE_RECIPIENT` is configured.
- [ ] `AGE_IDENTITY_FILE` points to a private age identity file outside Git.
- [ ] `RESTORE_DRILL_DATABASE=vatranscribe_restore_drill` is configured and differs from `POSTGRES_DB`.
- [ ] `infra/backup/run-backup-restore-proof.sh` completed on the production host.
- [ ] `infra/backup/validate-backup-artifacts.sh` verified checksum, manifest, encryption, and `pg_restore --list`.
- [ ] Restore drill completed into a disposable PostgreSQL database.
- [ ] `alembic_version` and critical tables were verified.
- [ ] `infra/backup/redact-backup-restore-report.sh` created sanitized `backup-restore-proof-evidence`.
- [ ] Sanitized evidence is stored outside Git.


## Remaining activation blocks

- P3-06 Legal / 152-ФЗ final operator data.
- P3-07 Supply-chain scan evidence.
- P3-08 Production rehearsal.

## Secret handling notice

DO NOT commit real secrets, runtime .env.runtime files, private keys, tokens, certificates, backup keys, payment keys, webhook secrets, SMTP passwords, Sentry DSNs, DNS/CDN API tokens, TLS private keys, Certbot account keys, or redacted evidence files to the repository.

## P3-06 Legal / 152-ФЗ activation

- [ ] Real operator details are filled locally and outside Git.
- [ ] Legal, privacy, and support contacts are real and monitored.
- [ ] Privacy Policy final review is complete.
- [ ] User Agreement / Terms final review is complete.
- [ ] Cookie Policy final review is complete.
- [ ] Consent to personal data processing final review is complete.
- [ ] Analytics/cookie consent final review is complete.
- [ ] 152-ФЗ applicability decision is recorded.
- [ ] RKN operator notification decision is recorded.
- [ ] Personal data localization decision is recorded.
- [ ] Cross-border transfer decision is recorded.
- [ ] Processors/subprocessors inventory is complete.
- [ ] Payment provider legal identity matches the operator before paid billing is enabled.
- [ ] Completed legal evidence is stored outside Git.
- [ ] Human/legal review gives PASS before public launch.

## P3-07 Supply-chain evidence

- [ ] Runtime environment and CI have scanner tools available: `pip-audit`, `npm`, Trivy, Gitleaks, and Syft.
- [ ] `scripts/security/run-supply-chain-evidence.ps1` or `.sh` completed for the release candidate.
- [ ] `pip-audit` report exists outside Git.
- [ ] `npm audit --workspaces --audit-level=high` report exists outside Git.
- [ ] Trivy filesystem/config/secret report exists outside Git.
- [ ] Gitleaks redacted report exists outside Git.
- [ ] Syft SBOM exists outside Git or in a controlled artifact store.
- [ ] High/Critical findings are fixed or have explicit release-owner triage.
- [ ] Medium findings are manually reviewed.
- [ ] Low findings are accepted or scheduled.
- [ ] Sanitized supply-chain evidence summary is available.
- [ ] Raw reports, SBOM files, tokens, credentials, private registry URLs, and unreviewed secret findings are not committed to Git.

## P3-07 secret handling notice

DO NOT commit raw scanner outputs, SBOM files, private registry URLs, real credentials, `.env` files, `.env.runtime`, GitHub tokens, npm tokens, container registry tokens, or unreviewed Gitleaks findings to the repository.
