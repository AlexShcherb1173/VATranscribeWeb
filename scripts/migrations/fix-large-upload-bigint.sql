-- VATranscribe large upload fix
-- Fixes PostgreSQL integer overflow for files larger than 2 GB.
-- Safe to run multiple times.

BEGIN;

ALTER TABLE IF EXISTS media_assets
    ALTER COLUMN size_bytes TYPE BIGINT
    USING size_bytes::BIGINT;

ALTER TABLE IF EXISTS export_artifacts
    ALTER COLUMN size_bytes TYPE BIGINT
    USING size_bytes::BIGINT;

ALTER TABLE IF EXISTS user_quotas
    ALTER COLUMN storage_bytes_used TYPE BIGINT
    USING storage_bytes_used::BIGINT,
    ALTER COLUMN storage_bytes_limit TYPE BIGINT
    USING storage_bytes_limit::BIGINT;

ALTER TABLE IF EXISTS usage_snapshots
    ALTER COLUMN storage_bytes_used TYPE BIGINT
    USING storage_bytes_used::BIGINT;

ALTER TABLE IF EXISTS plans
    ALTER COLUMN storage_bytes_limit TYPE BIGINT
    USING storage_bytes_limit::BIGINT;

COMMIT;
