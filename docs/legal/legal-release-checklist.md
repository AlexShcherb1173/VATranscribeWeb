# P2-01 Legal release checklist


VATranscribe release-readiness legal/compliance artifact.
## Must be completed before public production

- [ ] `LEGAL_OPERATOR_NAME` is real.
- [ ] `LEGAL_CONTACT_EMAIL` is real and monitored.
- [ ] `PRIVACY_CONTACT_EMAIL` is real and monitored.
- [ ] `SUPPORT_EMAIL` is real and monitored.
- [ ] `LEGAL_PRODUCTION_DOMAINS` contains real domains.
- [ ] `LEGAL_OPERATOR_ADDRESS` is filled if required for the chosen operator status.
- [ ] `LEGAL_OPERATOR_INN` is filled if applicable.
- [ ] `LEGAL_OPERATOR_OGRN` / `LEGAL_OPERATOR_OGRNIP` is filled if applicable.
- [ ] 152-FZ Russian personal data decision is recorded.
- [ ] RKN notification decision/status is recorded.
- [ ] Personal data localization decision/status is recorded.
- [ ] Third-party processors are either disabled or listed with country/purpose.
- [ ] Paid billing remains disabled until production payment gate is complete.
- [ ] Cookie consent UI is implemented before non-essential analytics or marketing pixels are enabled.
- [ ] Legal documents have been reviewed for the actual operator and target jurisdictions.

## Verification

Run:

```powershell
pytest tests/privacy/test_legal_compliance_finalization_static.py -v
pytest tests/privacy tests/security -v
npm --prefix apps/web run build
```
