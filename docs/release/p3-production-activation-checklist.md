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
