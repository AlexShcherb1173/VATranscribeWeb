# Supply-chain security policy

## Scope

This policy covers Python dependencies, Node dependencies, Docker build context, GitHub Actions, secret scanning, and SBOM generation for VATranscribeWeb.

## Release gate

A production release is blocked when any of the following are true:

- Critical or High vulnerability is detected by dependency, container, or configuration scan.
- Secret scanning finds a real credential or private key.
- Required lockfiles or dependency manifests are missing.
- A scan workflow is disabled or skipped without a documented release exception.

Medium findings require manual review and a triage note. Low findings may be accepted with review.

## Required tools

- `pip-audit` for Python packages.
- `npm audit` for Node workspaces.
- `Trivy` for filesystem, container, Dockerfile, and compose checks.
- `Gitleaks` for repository secret scanning.
- `Syft` for SBOM generation.

## Operational cadence

- Pull requests: security workflow runs automatically.
- Main/develop/feature branches: security workflow runs on push.
- Scheduled scan: weekly.
- Release candidate: run local scan and CI scan before tagging.
