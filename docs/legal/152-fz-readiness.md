# P2-01 152-FZ readiness

## Current status

P2-01 introduces technical controls and documents needed to avoid publishing neutral legal placeholders, but it does not by itself complete 152-FZ production compliance.

## Required production decisions

- Whether VATranscribe processes personal data of Russian citizens.
- Whether the operator must notify Roskomnadzor.
- Whether the primary personal data database is localized in Russia.
- Which hosting, backup, CDN, analytics, APM, email and payment providers are used.
- Which exact operator details are published.

## Technical controls added

- `LEGAL_*` environment settings.
- Production guardrails rejecting neutral operator/contact values.
- Backend legal documents generated from settings.
- Required registration documents remain `terms`, `privacy`, `personal_data`.
- Static tests for legal placeholders and production guards.

## Release rule

Do not switch `APP_ENV=production` for a public launch until real legal settings are supplied and the 152-FZ decisions are explicitly recorded.
