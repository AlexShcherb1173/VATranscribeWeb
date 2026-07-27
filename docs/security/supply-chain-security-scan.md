# P2-10 Supply-chain security scan

## Purpose

P2-10 adds the release gate for dependency, container, secret, and SBOM checks.

## Local scan

PowerShell:

```powershell
pwsh -ExecutionPolicy Bypass -File .\scripts\security\run-supply-chain-scan.ps1
```

Bash:

```bash
bash scripts/security/run-supply-chain-scan.sh
```

## CI scan

The GitHub Actions workflow `.github/workflows/security-scan.yml` runs:

- lockfile policy check;
- `pip-audit` for Python packages;
- `npm audit --workspaces --audit-level=high` for Node workspaces;
- Trivy filesystem/config/secret scan;
- Gitleaks repository secret scan;
- Syft SBOM generation.

## Release rule

Critical and high findings block production release. Medium findings require manual review. Low findings may be accepted with documented review.
