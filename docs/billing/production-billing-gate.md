# Production billing gate

## Status for P2-04

Payment provider is intentionally disabled until a real provider, webhook signing contract and fiscal receipt workflow are selected.

## Production rules

- `PAYMENT_PROVIDER=disabled` means paid plan activation is disabled.
- `BILLING_FAKE_UPGRADE_ENABLED=false` is mandatory in production.
- `/api/v1/billing/upgrade` must not activate a paid plan in production.
- Paid plan activation is allowed only from a verified payment webhook.
- Payment webhook signature verification is mandatory when `PAYMENT_PROVIDER` is enabled.
- Payment webhook processing is idempotent through `payment_events.provider_event_key`.
- Payment events are audit-logged.

## Development rules

`BILLING_FAKE_UPGRADE_ENABLED=true` may be used only outside production for local UI testing of quota and subscription flows.

## Provider contract

Before public paid launch choose a provider and document:

- provider name and region;
- checkout flow;
- webhook signature algorithm;
- event identifiers;
- refund/cancel flow;
- fiscal receipt responsibility;
- idempotency guarantees;
- failure handling.

## Fiscalization gate

Public paid launch is blocked until fiscal receipts / tax handling is resolved for the target market.
