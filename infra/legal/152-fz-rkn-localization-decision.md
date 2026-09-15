# P3-06 152-ФЗ / РКН / personal data localization decision

VATranscribeWeb production legal activation artifact.

## Default release stance

For production planning, treat 152-ФЗ as applicable when VATranscribeWeb may process personal data of Russian users.

The public launch is blocked until the following decisions are explicitly recorded and reviewed:

- 152-ФЗ applicability.
- Roskomnadzor operator notification status.
- Russian personal data localization status.
- Cross-border transfer status if non-Russian processors are used.
- Processor/subprocessor inventory.

## Decision table

| Decision | Required before launch | Current default | Evidence location |
|---|---:|---|---|
| Russian users can register or upload files | yes | possible | local legal evidence outside Git |
| Russian personal data is processed | yes | treat as applicable | local legal evidence outside Git |
| RKN operator notification is required | yes | requires legal review | local legal evidence outside Git |
| Primary Russian personal data database localization | yes | required if Russian PD is processed | local legal evidence outside Git |
| Cross-border transfer exists | yes | depends on processors | processors inventory |
| Sensitive/biometric data processing exists | yes | not intended | product/legal review |
| Public legal documents are final | yes | requires final review | final review checklist |

## Minimum 152-ФЗ analysis questions

- What personal data is collected during registration and profile management?
- Are uploaded audio/video/transcript files personal data or can they contain personal data?
- Are Russian citizens allowed to use the service?
- Where is the primary database physically hosted?
- Where are backups stored?
- Are CDN, analytics, Sentry/APM, email, payment, or support providers outside Russia?
- Are users clearly informed about purposes, retention, deletion, export, and processors?
- Is consent to personal data processing collected when required?
- Does the service need an RKN operator notification before public launch?

## Production blocker rule

Do not make a public production launch while any row below is unresolved:

```text
LEGAL_152FZ_RUSSIAN_PD=undecided
LEGAL_152FZ_RKN_NOTIFICATION_STATUS=undecided
LEGAL_152FZ_PD_LOCALIZATION_STATUS=undecided
LEGAL_CROSS_BORDER_TRANSFER_STATUS=undecided
```

## Localization evidence checklist

- [ ] Primary PostgreSQL database region is documented.
- [ ] Backup storage region is documented.
- [ ] Logs storage region is documented.
- [ ] Sentry/APM region or provider country is documented.
- [ ] CDN/DNS provider country is documented.
- [ ] Analytics provider country is documented.
- [ ] Payment provider country is documented.
- [ ] Email provider country is documented.

## Secret and personal data handling notice

DO NOT commit real personal data, private operator data, user exports, uploaded files, transcript samples, contracts with personal data, provider tokens, runtime secrets, or raw legal evidence to the repository.

This document is not legal advice. Final decisions must be validated against the actual processing activities and operator status.
