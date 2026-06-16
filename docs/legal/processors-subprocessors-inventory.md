# Processors and subprocessors inventory

VATranscribeWeb P3-06 release-readiness artifact.

## Required before production

Every provider that can receive personal data, request metadata, logs, analytics events, payment metadata, support messages, or encrypted backups must be listed and reviewed.

## Provider categories

- Hosting provider.
- Database provider if managed.
- Backup storage provider.
- DNS provider.
- CDN provider.
- Email provider.
- Payment provider.
- Sentry/APM provider.
- Analytics provider.
- Centralized logging provider.
- Support/CRM provider if used.

## Review table

| Provider category | Provider | Enabled | Data categories | Country/region | Legal basis / terms reviewed | Privacy document updated |
|---|---|---:|---|---|---:|---:|
| Hosting | <filled locally> | no | account data, files, logs | <filled locally> | no | no |
| Backup storage | <filled locally> | no | encrypted DB backups | <filled locally> | no | no |
| DNS/CDN | <filled locally> | no | IP/request metadata | <filled locally> | no | no |
| Email | <filled locally> | no | email address, email metadata | <filled locally> | no | no |
| Payment | disabled until production gate | no | payment metadata | <filled locally> | no | no |
| Sentry/APM | Sentry planned | no | error data, request metadata | <filled locally> | no | no |
| Analytics | disabled until consent/config | no | consented analytics events | <filled locally> | no | no |
| Logging | Loki/Grafana or external | no | request logs, request_id, IPs | <filled locally> | no | no |
| Support/CRM | optional | no | support messages | <filled locally> | no | no |

## Release rule

Do not enable a provider in production until it is present in this inventory and reflected in Privacy Policy / Cookie Policy where required.

## Secret handling notice

DO NOT commit API tokens, account IDs, contracts with personal data, rclone configuration, payment credentials, Sentry DSNs, SMTP credentials, or provider security keys to the repository.

This document is not legal advice. It is a structured input for final legal review.
