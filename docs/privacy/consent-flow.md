# Consent Flow

Stage 2.4 connects legal document versions with registration and user consent history.

Required document types:

- terms
- privacy
- personal_data

Registration must include accepted_legal_documents with current versions.

Backend behavior:

1. Ensures default active legal documents exist.
2. Validates submitted document types and versions.
3. Creates user.
4. Records rows in user_consents.
5. Writes audit event legal.consents_accepted.

Endpoints:

- GET /api/v1/legal/documents
- GET /api/v1/legal/documents/current
- GET /api/v1/legal/documents/{document_type}/current
- GET /api/v1/consents/me
- POST /api/v1/consents/accept-current
