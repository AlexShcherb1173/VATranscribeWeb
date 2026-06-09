# Privacy Requests

Stage 2.5 implements real privacy request persistence.

## Supported request types

- export
- delete_account
- delete_files
- revoke_consent

## Endpoints

- GET /api/v1/privacy/me
- POST /api/v1/privacy/requests

## Request lifecycle

New requests are created with status pending.

Future admin workflow should process requests and set:

- status
- processed_at

## Audit

Creating a privacy request writes audit event:

- privacy.request_created

## Security

Privacy requests are scoped to the authenticated user through current_user.id.
Users can see only their own privacy request history.
