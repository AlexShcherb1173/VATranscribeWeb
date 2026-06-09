# Stage 3.4 Legal Pages

Stage 3.4 replaces placeholder legal pages with structured legal document drafts.

## Marketing routes

- `/legal`
- `/legal/terms`
- `/legal/privacy`
- `/legal/personal-data`
- `/legal/cookies`
- `/legal/refund`

## Document versions

Current public legal document version:

- `1.0`

## Backend consent mapping

Backend required registration documents:

- `terms`
- `privacy`
- `personal_data`

Marketing routes:

- `terms` -> `/legal/terms`
- `privacy` -> `/legal/privacy`
- `personal_data` -> `/legal/personal-data`

Additional policy pages:

- `cookies` -> `/legal/cookies`
- `refund` -> `/legal/refund`

## Important production note

These pages are structured legal drafts, not legal advice. Before production launch:

- replace placeholder business details
- add legal entity name
- add registered address
- add legal/support/privacy/billing contact emails
- define jurisdiction and governing law
- finalize retention periods
- list actual processors and analytics providers
- finalize refund and cancellation policy
- review all documents with counsel