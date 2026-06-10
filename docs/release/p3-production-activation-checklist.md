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

## Remaining activation blocks

- P3-03 Domain / TLS / CDN live evidence.
- P3-04 Monitoring / APM / centralized logging live evidence.
- P3-05 Backup restore proof.
- P3-06 Legal / 152-ФЗ final operator data.
- P3-07 Supply-chain scan evidence.
- P3-08 Production rehearsal.

## Secret handling notice

DO NOT commit real secrets, runtime .env.runtime files, private keys, tokens, certificates, backup keys, payment keys, webhook secrets, SMTP passwords, Sentry DSNs, or redacted evidence files to the repository.
