# Stage 4 P2-10 — Supply-chain security scan

## Status

Planned outcome: release-readiness gate for supply-chain security.

## Components

- Dependabot configuration for GitHub Actions, Python, Node, and Docker.
- Security scan workflow.
- Local scan scripts for Windows and Unix-like environments.
- Lockfile policy checks.
- Secret scanning policy.
- SBOM documentation.
- Vulnerability triage process.

## Acceptance criteria

- Security scan workflow exists and runs on PR, push, schedule, and manual dispatch.
- Dependabot is configured.
- Local scan scripts exist.
- Critical and high findings are release blockers.
- Secret scanning is active.
- SBOM generation is available in CI.
- Static tests verify the configuration.
