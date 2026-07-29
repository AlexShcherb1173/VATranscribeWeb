# Secret scanning policy

## Rules

Real secrets must not be committed to the repository. This includes API keys, payment provider keys, webhook secrets, private keys, SSH keys, database passwords, OAuth secrets, analytics tokens, backup encryption keys, and production runtime env files.

## Scanners

- CI runs a strict Gitleaks Git-history scan on pull requests, pushes, weekly schedule, and manual dispatch.
- CI uses `.gitleaks.toml` with the built-in rules and no repository-wide allowlist.
- Local filesystem scans can be run through `scripts/security/run-supply-chain-scan.ps1` or `scripts/security/run-supply-chain-scan.sh`.
- Local scripts use `gitleaks dir . --config .gitleaks.local.toml`.

## Scanning modes

### Strict repository and history scan

`.gitleaks.toml` is used by CI and manual Git-history checks. Source code, documentation, security documentation, and example env files remain in scope. A path must not be excluded merely because it normally contains examples.

### Local filesystem scan

`.gitleaks.local.toml` extends the strict configuration and excludes only local dependencies, build outputs, authorized runtime secret files, and generated evidence directories. This prevents findings from `.venv` and `node_modules` from obscuring findings in project-owned files.

Local `.env` and runtime env files must remain excluded from Git. Excluding them from the local filesystem scan does not authorize committing them.

## Allowed examples

Example values may exist in example env files and documentation only when they are clearly non-secret. Example files and documentation remain scanned; broad path allowlists are prohibited. Production secrets must be supplied through GitHub Environments, runtime secret files, or a secret manager integration.

## Incident response

If a real secret is committed:

1. Revoke or rotate the secret immediately.
2. Remove it from current code.
3. Review Git history exposure and decide whether history rewrite is required.
4. Add a regression test or scanner rule if the pattern was missed.
5. Record the incident in the security notes.
