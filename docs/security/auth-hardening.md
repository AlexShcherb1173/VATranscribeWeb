# Auth Hardening

Stage 2 hardens authentication flows.

## Implemented controls

- Access JWT authentication
- Refresh token rotation
- Refresh token revocation
- Logout and logout-all
- Audit logs for auth events
- Rate limits for register, login and refresh
- Backend password policy on registration
- Required legal consents during registration

## Backend password policy

Registration rejects weak passwords before user creation.

Current policy:

- minimum length: 8 characters
- at least one uppercase letter
- at least one lowercase letter
- at least one digit

The backend calls:

validate_password_strength(payload.password)

If validation fails:

- user is not created
- response status is 422
- audit event auth.register_failed is written
- audit metadata contains reason=password_policy_failed

## Important

Frontend password checks are only UX. Backend validation is mandatory and is the source of truth.
