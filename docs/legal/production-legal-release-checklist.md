# Production legal release checklist

VATranscribeWeb P3-06 release-readiness artifact.

## Release status

P3-06 foundation creates the checklist and evidence workflow for final legal activation. It does not by itself make the service legally ready for public production.

Public production remains blocked until real operator data is filled locally and a final legal review is completed.

## Must be complete before public launch

- [ ] Real operator details are filled locally, outside Git.
- [ ] Legal contact is monitored.
- [ ] Privacy contact is monitored.
- [ ] Support contact is monitored.
- [ ] Privacy Policy has final review.
- [ ] User Agreement / Terms have final review.
- [ ] Cookie Policy has final review.
- [ ] Consent to personal data processing has final review.
- [ ] Analytics/cookie consent flow has final review.
- [ ] 152-ФЗ applicability decision is recorded.
- [ ] RKN operator notification decision is recorded.
- [ ] Russian personal data localization decision is recorded.
- [ ] Cross-border transfer decision is recorded.
- [ ] Processors/subprocessors inventory is complete.
- [ ] Payment provider legal identity matches the operator before paid billing is enabled.
- [ ] Production legal environment variables contain no neutral placeholders.
- [ ] Public legal pages and API legal documents are version-aligned.

## Required evidence files

Keep completed evidence outside Git:

- `legal-final-review-evidence-<date>.md`
- `processors-subprocessors-inventory-<date>.md`
- `152-fz-rkn-localization-decision-<date>.md`

Commit only sanitized templates.

## Production environment fields

```text
LEGAL_OPERATOR_TYPE=<filled locally>
LEGAL_OPERATOR_NAME=<filled locally>
LEGAL_OPERATOR_ADDRESS=<filled locally if required>
LEGAL_OPERATOR_INN=<filled locally if applicable>
LEGAL_OPERATOR_OGRN=<filled locally if applicable>
LEGAL_OPERATOR_OGRNIP=<filled locally if applicable>
LEGAL_CONTACT_EMAIL=legal@vatranscribe.ru
PRIVACY_CONTACT_EMAIL=privacy@vatranscribe.ru
SUPPORT_EMAIL=<filled locally>
LEGAL_152FZ_RUSSIAN_PD=<applicable/not_applicable after review>
LEGAL_152FZ_RKN_NOTIFICATION_STATUS=<notified/not_required/pending after review>
LEGAL_152FZ_PD_LOCALIZATION_STATUS=<localized/not_required/pending after review>
LEGAL_CROSS_BORDER_TRANSFER_STATUS=<none/exists/disabled after review>
```

## Secret and personal data handling notice

DO NOT commit private operator details, personal identifiers, private address, passport data, contracts with personal data, runtime `.env.runtime`, payment keys, provider tokens, or completed legal evidence to the repository.

This document is not legal advice. Use it as an engineering release gate and get qualified legal review before public launch.
