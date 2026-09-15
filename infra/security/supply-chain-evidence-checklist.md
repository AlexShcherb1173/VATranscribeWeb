# P3-07 Supply-chain evidence checklist

The release gate covers `pip-audit`, `npm audit`, `Trivy`, `Gitleaks`, and `Syft`.
High and Critical findings block release unless formally triaged and approved.
DO NOT commit raw reports, credentials, tokens, environment files, or unredacted scan output.

## Required checks

- [ ] `pip-audit` completed.
- [ ] `npm audit` completed.
- [ ] `Trivy` completed.
- [ ] `Gitleaks` completed.
- [ ] `Syft` SBOM generated.
- [ ] High findings are zero or approved.
- [ ] Critical findings are zero.
- [ ] Redacted evidence reviewed.
