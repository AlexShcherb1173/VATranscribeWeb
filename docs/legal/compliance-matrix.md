# P2-01 Legal / compliance matrix


VATranscribe release-readiness legal/compliance artifact.
Status: foundation ready, public production still blocked until real operator details are supplied.

## Operator

- Operator type: individual / self-employed.
- Operator name: configured by `LEGAL_OPERATOR_NAME`.
- Legal contact: configured by `LEGAL_CONTACT_EMAIL`.
- Privacy contact: configured by `PRIVACY_CONTACT_EMAIL`.
- Support contact: configured by `SUPPORT_EMAIL`.

Production guardrails reject neutral example values in `APP_ENV=production`.

## Documents

| Document | API type | Required for registration | Version |
|---|---|---:|---|
| User Agreement / Terms of Service | `terms` | yes | `LEGAL_DOCUMENT_VERSION` |
| Privacy Policy | `privacy` | yes | `LEGAL_DOCUMENT_VERSION` |
| Consent to Personal Data Processing | `personal_data` | yes | `LEGAL_DOCUMENT_VERSION` |
| Cookie Policy | `cookies` | no | `LEGAL_DOCUMENT_VERSION` |
| Refund Policy | `refund` | no | `LEGAL_DOCUMENT_VERSION` |

## Release blockers after P2-01

- Replace neutral legal contacts with real contacts.
- Add real operator name, address, INN and OGRN/OGRNIP if applicable.
- Decide whether Russian citizens' personal data is processed.
- Decide RKN notification status.
- Decide personal data localization status.
- Keep third-party processors disabled or list real providers.
- Do not enable paid billing until P2-04 billing production gate is complete.

This document is not legal advice. Final public legal text should be reviewed against the actual business status and target jurisdictions.
