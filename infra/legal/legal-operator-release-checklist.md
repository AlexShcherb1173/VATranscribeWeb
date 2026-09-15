# P3-06 Legal operator release checklist

VATranscribeWeb legal activation artifact.

Purpose: make the operator identity and public legal contacts ready for production without committing private identity documents, secrets, or unreviewed legal text.

## Scope

- Public operator details for VATranscribeWeb.
- Public legal, privacy and support contacts.
- Domain and document ownership consistency.
- 152-ФЗ / РКН / personal data localization decisions.
- Human legal review before public launch.

## Operator data checklist

Complete locally before public production:

- [ ] Real operator name is filled locally in production settings.
- [ ] Operator type is selected: individual, self-employed, individual entrepreneur, company, or other legally reviewed status.
- [ ] Public legal contact email is monitored: `legal@vatranscribe.ru` or another reviewed address.
- [ ] Public privacy contact email is monitored: `privacy@vatranscribe.ru` or another reviewed address.
- [ ] Public support email is monitored.
- [ ] Operator address is filled only if required for the selected operator status and jurisdiction.
- [ ] INN / OGRN / OGRNIP is filled only if applicable and approved for publication.
- [ ] Domain ownership and published legal pages match the operator.
- [ ] Payment provider merchant profile matches the same operator before paid billing is enabled.

## Local-only fields

Use local production settings or a private legal evidence file outside Git:

```text
LEGAL_OPERATOR_NAME=<filled locally>
LEGAL_OPERATOR_TYPE=<filled locally>
LEGAL_OPERATOR_ADDRESS=<filled locally if required>
LEGAL_OPERATOR_INN=<filled locally if applicable>
LEGAL_OPERATOR_OGRN=<filled locally if applicable>
LEGAL_OPERATOR_OGRNIP=<filled locally if applicable>
LEGAL_CONTACT_EMAIL=legal@vatranscribe.ru
PRIVACY_CONTACT_EMAIL=privacy@vatranscribe.ru
SUPPORT_EMAIL=<filled locally>
```

## Release blockers

- [ ] `LEGAL_OPERATOR_NAME` is still neutral, generic, or empty.
- [ ] Legal or privacy email is not monitored.
- [ ] Published documents identify an operator that does not match payment, domain, or hosting records.
- [ ] 152-ФЗ decision is not recorded.
- [ ] RKN notification decision is not recorded.
- [ ] Personal data localization decision is not recorded.
- [ ] Human final review is not complete.

## Secret and personal data handling notice

DO NOT commit passport data, private address details, personal identifiers, scans, contracts with personal data, runtime `.env.runtime` files, provider tokens, payment keys, or legal evidence with private operator data to the repository.

This document is not legal advice. Final release should be reviewed by a qualified lawyer for the actual operator, target users, payment model, and jurisdictions.
