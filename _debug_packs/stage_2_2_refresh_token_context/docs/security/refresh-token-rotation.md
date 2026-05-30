# Refresh Token Rotation

Refresh tokens must be stored as hashes.

Flow:
1. User logs in.
2. API issues access token and refresh token.
3. Refresh token hash is stored in DB.
4. On refresh, old token is revoked.
5. New refresh token is issued and stored.
6. Reuse of revoked token is treated as security event.
