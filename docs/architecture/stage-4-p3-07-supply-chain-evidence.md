# Stage 4 / P3-07 Supply-chain evidence

## Status

Foundation target: supply-chain evidence workflow for production activation.

## Decisions

- Python scanner: `pip-audit`.
- Node scanner: `npm audit`.
- Filesystem/config/secret scanner: Trivy.
- Repository secret scanner: Gitleaks.
- SBOM generator: Syft.
- Release-blocking severity: High and Critical.
- Medium findings: manual review.
- Low findings: documented acceptance allowed.

## Added controls

- `scripts/security/run-supply-chain-evidence.ps1`
- `scripts/security/run-supply-chain-evidence.sh`
- `scripts/security/redact-supply-chain-evidence.ps1`
- `scripts/security/redact-supply-chain-evidence.sh`
- `infra/security/supply-chain-evidence-checklist.md`
- `infra/security/supply-chain-evidence-template.md`
- `infra/security/vulnerability-triage-high-critical.md`

## Production evidence requirements

- `pip-audit` evidence.
- `npm audit` evidence.
- Trivy evidence.
- Gitleaks evidence.
- Syft SBOM evidence.
- Triage record for each High/Critical finding.
- Sanitized release decision summary stored outside Git or copied into a reviewed release record.

## Secret handling notice

DO NOT commit raw scan reports, SBOM files, private registry URLs, tokens, credentials, runtime env files, or unreviewed Gitleaks findings to the repository.
