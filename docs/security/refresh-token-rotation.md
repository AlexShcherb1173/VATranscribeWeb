# Refresh Token Rotation

Stage 2.2 implements refresh token rotation in the real auth flow.

## Endpoints

- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- POST /api/v1/auth/logout-all

## Login

Login returns:
- access_token
- refresh_token
- token_type

## Refresh

Refresh token flow:
1. Client sends refresh_token.
2. API hashes token and finds active DB record.
3. API rejects missing, revoked or expired tokens.
4. API revokes old token.
5. API creates a new refresh token.
6. API returns a new access_token and refresh_token.

## Logout

Logout revokes the provided refresh token.

## Logout all

Logout all requires current access token and revokes all active refresh tokens for current user.

## Storage rule

Only refresh token hashes are stored in DB. Raw refresh tokens are returned only once to the client.
