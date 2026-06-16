# 152-ФЗ / РКН / localization decision checklist

VATranscribeWeb P3-06 release-readiness artifact.

## Required production decision

Because VATranscribeWeb may allow Russian users to register, upload files, create transcripts, request exports, and communicate with support, the release process must treat Russian personal data compliance as a blocker until reviewed.

## Decision checklist

- [ ] Decide whether the product processes personal data of Russian citizens.
- [ ] Decide whether an RKN operator notification is required before public launch.
- [ ] Decide whether the primary personal data database must be localized in Russia.
- [ ] Decide where encrypted backups may be stored.
- [ ] Decide whether logs can contain personal data and where they are stored.
- [ ] Decide whether Sentry/APM, analytics, email, CDN, payment, or support tools create cross-border transfers.
- [ ] Decide whether uploaded media/transcripts can contain personal data and whether extra restrictions are needed.
- [ ] Decide whether any sensitive or biometric data processing may occur.
- [ ] Record all decisions in local legal evidence outside Git.

## Recommended blocker rule

Production launch should stay blocked while any of these values are unresolved:

```text
LEGAL_152FZ_RUSSIAN_PD=undecided
LEGAL_152FZ_RKN_NOTIFICATION_STATUS=undecided
LEGAL_152FZ_PD_LOCALIZATION_STATUS=undecided
LEGAL_CROSS_BORDER_TRANSFER_STATUS=undecided
```

## Evidence summary template

```text
152-ФЗ applicability: <filled locally>
RKN notification status: <filled locally>
Personal data localization status: <filled locally>
Cross-border transfer status: <filled locally>
Legal reviewer: <filled locally>
Decision date: <filled locally>
Release decision: PASS / BLOCKED
```

## Secret and personal data handling notice

DO NOT commit completed 152-ФЗ evidence with private operator data, user data, provider account details, runtime secrets, contracts, or personal identifiers to the repository.

This document is not legal advice. Final decisions must be reviewed against the actual data processing model and operator status.
