# Stage 4 / P2-02 — Admin 2FA

## Goal

Close the release blocker: admin access must require two-factor authentication.

## Implemented controls

- `users.is_admin` database-backed admin role flag.
- `admin_two_factor` table for enabled and pending TOTP secrets.
- `admin_recovery_codes` table for hashed one-time recovery codes.
- `require_admin_user` dependency for role enforcement.
- `require_admin_2fa` dependency for protected admin functions.
- Admin 2FA endpoints under `/api/v1/admin/security`.
- Audit events for setup, confirmation, disable and recovery-code rotation.
- Production config guardrails for `ADMIN_2FA_REQUIRED` and `ADMIN_2FA_ISSUER`.

## Security notes

TOTP secrets are encrypted at rest using an application-derived Fernet key. Recovery codes are never stored in plaintext; they are PBKDF2-hashed and single-use.

Setup and confirmation endpoints require an authenticated admin user but not completed 2FA, so the first admin can enroll. Operational bootstrap must be restricted to trusted operators.

## Validation

Static and service tests:

```bash
pytest tests/security/test_admin_2fa_static.py -v
pytest tests/security/test_admin_2fa_service.py -v
```

Migration:

```bash
python -m alembic upgrade head
```
