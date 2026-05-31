# Rate Limits

Stage 2.6 adds rate limits to auth endpoints.

## Current protected endpoints

- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh

## Limits

Development defaults:

- register: 5 requests / 10 minutes / IP
- login: 10 requests / 5 minutes / email + IP
- refresh: 30 requests / 5 minutes / IP

## Audit

When a request is blocked by the limiter, backend writes audit event:

- auth.rate_limited

Metadata includes:

- limited_action
- limit
- window_seconds
- email_mask, when available

## Implementation note

Current implementation uses an in-memory limiter. This is acceptable for local development and first foundation stage.

Production should replace it with Redis-based distributed rate limiting, because in-memory limits are per API process and do not work correctly across multiple replicas.
