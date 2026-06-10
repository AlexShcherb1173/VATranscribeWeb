# Stage 4 P2-09 — 404/500 + placeholder sweep

## Status

P2-09 adds final user-facing error and placeholder controls before the supply-chain security scan.

## Controls

- Marketing 404/500 pages are localized and marked `noindex`.
- Web app has a catch-all route and a production-safe error boundary.
- API exception handlers normalize 404/422/500 responses and avoid stack traces in production.
- Public legal contact placeholders are replaced with `@vatranscribe.ru` contact aliases.
- Payment placeholder language is replaced with production-safe disabled-billing language.
- Static tests verify the user-facing no-placeholder policy.

## Remaining operational work

Before public launch, confirm that all contact aliases are backed by real mailboxes and that the production legal operator details are finalized in runtime legal settings.
