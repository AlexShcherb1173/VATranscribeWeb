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

## Gitleaks scan modes

The local security scripts run:

```text
gitleaks dir . --config .gitleaks.local.toml --redact=100
```

The local configuration excludes local dependency directories, build outputs, runtime env files, and generated evidence. Project source files, documentation, `.env.example`, and `.env.production.example` remain in scope.

For a strict manual Git-history scan, run:

```text
gitleaks git . --config .gitleaks.toml --log-opts="--all" --redact=100
```

Raw JSON reports must be stored outside the repository or in an ignored evidence directory.

## CI scan

The GitHub Actions workflow `.github/workflows/security-scan.yml` runs:

- lockfile policy check;
- `pip-audit` for Python packages;
- `npm audit --workspaces --audit-level=high` for Node workspaces;
- Trivy filesystem/config/secret scan;
- Gitleaks strict Git-history scan using `.gitleaks.toml` and a full checkout history;
- Syft SBOM generation.

The Gitleaks CI job uses `fetch-depth: 0` and does not use the local filesystem allowlist.

## Release rule

Critical and high findings block production release. Medium findings require manual review. Low findings may be accepted with documented review.
