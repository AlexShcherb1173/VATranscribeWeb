# File Ownership and User Isolation

Every user-owned object must be selected with current_user.id.

Protected object groups:
- jobs
- media_assets
- transcripts
- export_artifacts
- uploads
- downloads
- transcription jobs

Required rule:
Do not fetch user-owned objects by id only.

Correct pattern:
select(Entity).where(Entity.id == id, Entity.user_id == current_user.id)

For indirect ownership:
ExportArtifact -> Transcript -> MediaAsset -> user_id

Generic job creation must validate transcription_media_asset_id before creating a job.
