# File Ownership and User Isolation

Every user-owned object must be selected with current_user.id.

## Protected object groups

- jobs
- media_assets
- transcripts
- export_artifacts
- uploads
- downloads
- transcription jobs

## Required rule

Do not fetch user-owned objects by id only.

Correct direct ownership pattern:

select(Entity).where(Entity.id == entity_id, Entity.user_id == current_user.id)

Correct indirect ownership pattern:

ExportArtifact -> Transcript -> MediaAsset -> user_id

## POST /jobs rule

POST /api/v1/jobs must validate payload.transcription_media_asset_id before creating Job.

Required check:

if payload.transcription_media_asset_id:
    get_user_media_asset_or_404(
        db=db,
        current_user=current_user,
        media_asset_id=payload.transcription_media_asset_id,
    )

This prevents a user from creating a generic job that references another user's MediaAsset.
