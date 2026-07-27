# Secret scanning policy

## Rules

Real secrets must not be committed to the repository. This includes API keys, payment provider keys, webhook secrets, private keys, SSH keys, database passwords, OAuth secrets, analytics tokens, backup encryption keys, and production runtime env files.

## Scanners

- CI runs Gitleaks on pull requests, pushes, weekly schedule, and manual dispatch.
- Local scans can be run through `scripts/security/run-supply-chain-scan.ps1` or `scripts/security/run-supply-chain-scan.sh`.

## Allowed examples

Example values may exist only in example env files and documentation, and must be clearly non-secret. Production secrets must be supplied through GitHub Environments, runtime secret files, or a future secret manager integration.

## Incident response

If a real secret is committed:

1. Revoke or rotate the secret immediately.
2. Remove it from current code.
3. Review Git history exposure and decide whether history rewrite is required.
4. Add a regression test or scanner rule if the pattern was missed.
5. Record the incident in the security notes.
