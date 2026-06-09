from __future__ import annotations

from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_settings_define_upload_download_retention_limits() -> None:
    text = read("apps/api/app/config.py")
    for name in [
        "max_upload_bytes",
        "upload_stream_chunk_bytes",
        "max_external_download_bytes",
        "max_export_artifact_bytes",
        "max_media_download_bytes",
        "temp_file_retention_hours",
        "failed_job_file_retention_days",
        "export_artifact_retention_days",
        "media_asset_retention_days",
        "transcript_retention_days",
        "cleanup_batch_size",
    ]:
        assert name in text


def test_env_examples_document_limits() -> None:
    for path in [".env.example", ".env.production.example"]:
        text = read(path)
        assert "MAX_UPLOAD_BYTES=1073741824" in text
        assert "MAX_EXTERNAL_DOWNLOAD_BYTES=2147483648" in text
        assert "MAX_EXPORT_ARTIFACT_BYTES=524288000" in text
        assert "MAX_MEDIA_DOWNLOAD_BYTES=2147483648" in text
        assert "TEMP_FILE_RETENTION_HOURS=24" in text
        assert "CLEANUP_BATCH_SIZE=500" in text


def test_upload_router_rejects_content_length_and_bounds_streaming_read() -> None:
    text = read("apps/api/app/routers/uploads.py")
    assert "parse_content_length(request.headers)" in text
    assert "settings.max_upload_bytes" in text
    assert "settings.upload_stream_chunk_bytes" in text
    assert "assert_can_store_bytes(db, current_user, known_size_bytes)" in text

    helper = read("apps/api/app/services/upload_helpers.py")
    assert "max_bytes: int | None" in helper
    assert "total_size > max_bytes" in helper
    assert "FileSizeLimitExceeded" in helper
    assert "target_path.unlink" in helper


def test_download_and_export_file_responses_have_size_guards() -> None:
    files = [
        "apps/api/app/routers/media_assets.py",
        "apps/api/app/routers/export_artifacts.py",
        "apps/api/app/routers/transcripts.py",
    ]
    joined = "\n".join(read(path) for path in files)
    assert "assert_path_size_within_limit" in joined
    assert "settings.max_media_download_bytes" in joined
    assert "settings.max_export_artifact_bytes" in joined


def test_quota_service_counts_media_and_export_artifacts() -> None:
    text = read("apps/api/app/services/quota_service.py")
    assert "def calculate_storage_usage_bytes" in text
    assert "select(MediaAsset.size_bytes)" in text
    assert "select(ExportArtifact.size_bytes)" in text
    assert "quota.storage_bytes_used = calculate_storage_usage_bytes" in text


def test_worker_enforces_external_download_limit_and_cleanup_task() -> None:
    text = read("apps/worker/app/tasks/jobs.py")
    assert "_make_limited_download_progress_hook" in text
    assert "settings.max_external_download_bytes" in text
    assert "assert_path_size_within_limit(final_path" in text
    assert "vatranscribe.storage.cleanup" in text
    assert "cleanup_storage_retention" in text


def test_retention_service_has_expected_cleanup_surfaces() -> None:
    text = read("apps/api/app/services/storage_retention.py")
    for name in [
        "cleanup_temp_files",
        "cleanup_failed_job_files",
        "cleanup_expired_export_artifacts",
        "cleanup_expired_media_assets",
        "cleanup_expired_transcripts",
        "cleanup_storage_retention",
    ]:
        assert name in text
