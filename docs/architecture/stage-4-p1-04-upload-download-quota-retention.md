# Stage 4 P1-04 — Upload/download limits, quota, retention

## Status

`P1-04_upload_download_limits_quota_retention` adds application-level limits and storage cleanup controls on top of the Nginx body limits from P1-01.

## Defaults

- `MAX_UPLOAD_BYTES=1073741824` — 1 GiB upload cap.
- `UPLOAD_STREAM_CHUNK_BYTES=1048576` — 1 MiB streaming read chunk.
- `MAX_EXTERNAL_DOWNLOAD_BYTES=2147483648` — 2 GiB external download cap.
- `MAX_EXPORT_ARTIFACT_BYTES=524288000` — 500 MiB export artifact cap.
- `MAX_MEDIA_DOWNLOAD_BYTES=2147483648` — 2 GiB media download response cap.
- `TEMP_FILE_RETENTION_HOURS=24`.
- `FAILED_JOB_FILE_RETENTION_DAYS=7`.
- `EXPORT_ARTIFACT_RETENTION_DAYS=14`.
- `MEDIA_ASSET_RETENTION_DAYS=30`.
- `TRANSCRIPT_RETENTION_DAYS=90`.
- `CLEANUP_BATCH_SIZE=500`.

## Upload controls

The upload endpoint rejects requests early when `Content-Length` exceeds `MAX_UPLOAD_BYTES`. If `Content-Length` is missing or inaccurate, the streaming save loop stops when the accumulated bytes exceed `MAX_UPLOAD_BYTES` and deletes the partial file.

## Download/export controls

Media and export download responses verify the file size before returning `FileResponse`. Worker download jobs enforce the external download cap through progress hooks and a final file-size check.

## Quota accounting

Storage quota sync now includes both `media_assets.size_bytes` and linked `export_artifacts.size_bytes`. Uploads check quota before saving when size is known and after saving when exact size is known. Deletion flows resync storage usage after removing media/export artifacts.

## Retention cleanup

`apps.api.app.services.storage_retention.cleanup_storage_retention()` provides a single cleanup entry point. A Celery task is exposed as `vatranscribe.storage.cleanup`; production can call it from Celery Beat, cron, or deployment scheduler.

## Remaining production follow-up

`yt-dlp` networking still needs container/network-level egress controls in `P1-05_container_production_hardening`; application hooks reduce exposure but do not replace network policy.
