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

## Remaining activation blocks

- P3-04 Monitoring / APM / centralized logging live evidence.
- P3-05 Backup restore proof.
- P3-06 Legal / 152-ФЗ final operator data.
- P3-07 Supply-chain scan evidence.
- P3-08 Production rehearsal.

## Secret handling notice

DO NOT commit real secrets, runtime .env.runtime files, private keys, tokens, certificates, backup keys, payment keys, webhook secrets, SMTP passwords, Sentry DSNs, DNS/CDN API tokens, TLS private keys, Certbot account keys, or redacted evidence files to the repository.
