# Stage 4 / P0-01 — Private storage access

Status: implemented by pply_P0-01_storage_private_access.ps1.

## Goal

/storage must not be a public HTTP surface. User files, generated exports and transcript artifacts must be downloadable only through authenticated owner-scoped API endpoints.

## Applied changes

- Removed FastAPI StaticFiles mount for /storage.
- Removed Nginx location /storage/ proxy.
- Removed Vite dev proxy for /storage.
- Removed internal filesystem path fields from public API schemas, media responses and nested job media payloads.
- Removed frontend rendering of internal storage paths.
- Switched export artifact and job cleanup filesystem resolution to esolve_storage_path().
- Added static guard tests for the public storage policy.

## Current parameters

- MAX_UPLOAD_MB: 1024
- FILE_RETENTION_DAYS: 30

These values are recorded for the Stage 4 roadmap. Hard enforcement of upload size, quota and retention should be finalized in the next P1/P2 patches.

## Required verification

Run from repository root:

`powershell
pytest tests/security/test_storage_private_access_static.py
`

Then run the normal checks:

`powershell
pytest apps/api/tests
npm --prefix apps/web run build
`

## Acceptance criteria

- GET /storage/... returns 404/403 and never returns files.
- Nginx does not proxy /storage/.
- Frontend does not use /storage URLs.
- API responses do not expose internal filesystem paths.
- Media downloads use /api/v1/media-assets/{id}/download or equivalent authenticated endpoints.
- Export downloads use /api/v1/transcripts/export-artifacts/{id}/download or equivalent authenticated endpoints.
- User A cannot download User B files.