# Stage 4 / P2-04 — Billing production gate

## Objective

Prevent development-only billing paths from activating paid plans in production.

## Implemented controls

- `PAYMENT_PROVIDER` configuration with provider allow-list.
- `BILLING_FAKE_UPGRADE_ENABLED` must be false in production.
- `BILLING_PAID_PLANS_ENABLED` cannot be true with `PAYMENT_PROVIDER=disabled`.
- `/billing/upgrade` requires `settings.fake_billing_upgrade_allowed` to activate paid plans manually.
- Verified payment webhook foundation under `/payment-webhooks/{provider}`.
- HMAC SHA-256 webhook signature helper.
- `payment_events` table for idempotency.
- Audit events for blocked, failed, ignored and processed payment events.

## Current production posture

Payment provider is disabled. Paid plans are not production-ready until provider integration and fiscal receipt requirements are completed.
