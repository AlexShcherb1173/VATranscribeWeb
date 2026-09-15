# Supply-chain evidence

P3-07 requires reproducible and redacted supply-chain evidence.

The release gate covers `pip-audit`, `npm audit`, `Trivy`, `Gitleaks`, and `Syft`.
High and Critical findings block release unless formally triaged and approved.
DO NOT commit raw reports, credentials, tokens, environment files, or unredacted scan output.

## Required release evidence

1. Run `pip-audit` for Python dependencies.
2. Run `npm audit` for npm workspaces.
3. Run `Trivy` for images and configuration.
4. Run `Gitleaks` against repository history.
5. Generate an SBOM with `Syft`.

## Acceptance criteria

- Critical findings must be zero.
- High findings must be zero or formally accepted.
- Raw reports remain outside Git.
- Only redacted summaries and report hashes are retained.
