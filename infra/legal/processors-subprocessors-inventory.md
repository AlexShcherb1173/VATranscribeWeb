# P3-06 Processors and subprocessors inventory

VATranscribeWeb production legal activation artifact.

Purpose: record all providers that may process personal data, metadata, telemetry, payment information, logs, backups, or support requests.

## Inventory table

Fill this table locally before public production. Keep contracts, DPAs, tokens, and account details outside Git.

| Category | Provider | Purpose | Data categories | Country/region | Enabled in production | DPA/terms reviewed | Cross-border transfer |
|---|---|---|---|---|---:|---:|---:|
| Hosting | <filled locally> | app/API/database hosting | account data, files, logs | <filled locally> | no | no | undecided |
| DNS/CDN | provider-neutral for now | DNS, TLS, static delivery | IP addresses, request metadata | <filled locally> | no | no | undecided |
| Analytics | disabled by default | product analytics | consented analytics events | <filled locally> | no | no | undecided |
| APM | Sentry planned | error monitoring, traces | errors, request metadata | <filled locally> | no | no | undecided |
| Email | <filled locally> | transactional/support email | email address, message metadata | <filled locally> | no | no | undecided |
| Payment | disabled until production gate | payment processing | payment metadata | <filled locally> | no | no | undecided |
| Backup storage | local/S3-compatible planned | encrypted backups | encrypted database backups | <filled locally> | no | no | undecided |
| Logging | Loki/Grafana or external provider | centralized logs | request IDs, IPs, errors | <filled locally> | no | no | undecided |
| Support/CRM | optional | support communication | contact data, support messages | <filled locally> | no | no | undecided |

## Provider activation checklist

For each provider enabled in production:

- [ ] Provider is listed in this inventory.
- [ ] Purpose is documented.
- [ ] Data categories are documented.
- [ ] Country/region is documented.
- [ ] Contract, DPA, or public terms are reviewed.
- [ ] Cross-border transfer decision is recorded.
- [ ] Privacy Policy names or categorizes the provider as required.
- [ ] Cookie Policy covers provider cookies if applicable.
- [ ] Retention and deletion behavior is known.
- [ ] Provider secrets are stored outside Git.

## Special notes

- Analytics and marketing pixels must remain consent-gated.
- Payment provider must remain disabled until production billing gate and merchant legal identity are aligned.
- API and authenticated user data must not be cached by CDN.
- Uploaded user files and transcripts must not be sent to optional processors unless explicitly documented and legally reviewed.

## Secret handling notice

DO NOT commit provider tokens, contracts with personal data, rclone configuration, API keys, DSNs, webhook secrets, or real account identifiers to the repository.

This document is not legal advice. It is an operational inventory for legal review and release readiness.
