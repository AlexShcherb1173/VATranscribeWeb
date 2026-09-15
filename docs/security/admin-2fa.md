# Admin 2FA

Status: P2-02 foundation.

VATranscribe admin access is protected by a two-layer gate:

1. `require_admin_user` checks the database-backed `users.is_admin` flag.
2. `require_admin_2fa` requires enabled TOTP two-factor authentication when `ADMIN_2FA_REQUIRED=true`.

## Method

The initial production method is TOTP with standard 30-second SHA-1 codes compatible with authenticator applications.

Endpoints:

- `GET /api/v1/admin/security/2fa/status`
- `POST /api/v1/admin/security/2fa/setup`
- `POST /api/v1/admin/security/2fa/confirm`
- `POST /api/v1/admin/security/2fa/disable`
- `POST /api/v1/admin/security/2fa/recovery-codes/rotate`
- `GET /api/v1/admin/security/check`

## Recovery codes

Recovery codes are shown only once after setup or rotation. They are stored only as PBKDF2 hashes and are single-use.

## Production policy

`APP_ENV=production` requires:

- `ADMIN_2FA_REQUIRED=true`;
- a non-placeholder `ADMIN_2FA_ISSUER`;
- admin-only routes using `require_admin_user`;
- sensitive admin routes using `require_admin_2fa`.

## Admin bootstrap

The admin flag is database-backed. Initial production admin assignment must be done through a controlled operational procedure, not via a permanent public endpoint.

Example SQL for a one-time bootstrap on a protected production console:

```sql
UPDATE users SET is_admin = true WHERE email = 'admin@example.com';
```

After bootstrap, the admin must complete TOTP setup before protected admin functionality is available.
