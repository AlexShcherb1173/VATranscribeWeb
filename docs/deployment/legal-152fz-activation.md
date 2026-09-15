# P3-06 Legal / 152-ФЗ activation

VATranscribeWeb deployment runbook.

## Goal

Activate the production legal release gate for operator data, 152-ФЗ decisions, RKN notification status, personal data localization, processors inventory, and final review of Privacy Policy / Terms / Cookies.

## Files added by P3-06

- `infra/legal/legal-operator-release-checklist.md`
- `infra/legal/152-fz-rkn-localization-decision.md`
- `infra/legal/processors-subprocessors-inventory.md`
- `infra/legal/legal-final-review-evidence-template.md`
- `infra/legal/privacy-terms-cookies-final-review.md`
- `docs/legal/production-legal-release-checklist.md`
- `docs/legal/152-fz-rkn-localization-decision.md`
- `docs/legal/processors-subprocessors-inventory.md`

## Activation steps

1. Fill real operator details locally in the production secret/runtime environment.
2. Confirm monitored emails for legal, privacy, and support.
3. Complete Privacy Policy final review.
4. Complete User Agreement / Terms final review.
5. Complete Cookie Policy final review.
6. Complete personal data processing consent final review.
7. Complete 152-ФЗ / РКН / localization decision checklist.
8. Complete processors/subprocessors inventory.
9. Store completed evidence outside Git.
10. Run privacy tests and production config validation.

## Suggested verification commands

```powershell
python -m pytest tests/privacy/test_legal_152fz_activation_static.py -v
python -m pytest tests/privacy -v
npm --prefix apps/marketing run build
npm --prefix apps/web run build
```

## Production blocker rule

Public launch stays blocked if:

- operator details are neutral or missing;
- legal or privacy email is not monitored;
- 152-ФЗ / РКН / localization decisions are unresolved;
- processors inventory is incomplete;
- final human/legal review is not complete.

## Secret and personal data handling notice

DO NOT commit real operator private data, passport data, contracts, personal identifiers, runtime secrets, payment credentials, provider tokens, or completed legal evidence to the repository.

This runbook is not legal advice. It is an operational release-control document.
