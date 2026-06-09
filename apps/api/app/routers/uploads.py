from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from apps.api.app.config import settings
from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import Job, JobLog, JobStatus, JobType, MediaAsset, SourceType, User
from apps.api.app.schemas import MediaAssetResponse
from apps.api.app.security_foundation.rate_limits import build_rate_limit_key, rate_limiter
from apps.api.app.services.quota_service import (
    assert_can_create_job,
    assert_can_store_bytes,
    increment_jobs_used,
    increment_storage_used,
)
from apps.api.app.services.upload_helpers import (
    build_upload_dir,
    detect_kind,
    guess_mime_type,
    safe_file_name,
    save_upload_file,
)

router = APIRouter(prefix="/uploads")


def build_media_asset_response(item: MediaAsset) -> MediaAssetResponse:
    return MediaAssetResponse(
        id=item.id,
        kind=item.kind,
        original_name=item.original_name,
        stored_name=item.stored_name,
        mime_type=item.mime_type,
        extension=item.extension,
        size_bytes=item.size_bytes,
        duration_sec=item.duration_sec,
        path=item.path,
        checksum_sha256=item.checksum_sha256,
        created_at=item.created_at,
        download_url=f"/api/v1/media-assets/{item.id}/download",
    )


def build_unique_stored_name(upload_dir: Path, original_name: str) -> str:
    safe_name = safe_file_name(original_name)
    stem = Path(safe_name).stem
    suffix = Path(safe_name).suffix

    candidate = safe_name
    counter = 1

    while (upload_dir / candidate).exists():
        candidate = f"{stem} ({counter}){suffix}"
        counter += 1

    return candidate


def _add_job_log(db: Session, job_id: str, level: str, message: str) -> None:
    db.add(JobLog(job_id=job_id, level=level, message=message))
    db.commit()


def _create_upload_job(
    db: Session,
    current_user: User,
    original_name: str,
    extension: str,
    known_size_bytes: int | None,
) -> Job:
    assert_can_create_job(db, current_user, jobs_to_add=1)

    job = Job(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        type=JobType.UPLOAD.value,
        status=JobStatus.RUNNING.value,
        source_type=SourceType.UPLOAD.value,
        title=f"Upload {original_name}",
        requested_file_name=original_name,
        requested_format=extension.lstrip(".") or None,
        progress_percent=5,
        progress_stage="uploading",
        progress_message="Upload started",
        started_at=datetime.now(timezone.utc),
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    increment_jobs_used(db, current_user, 1)
    _add_job_log(db, job.id, "INFO", f"Upload job created for {original_name}")

    if known_size_bytes is not None:
        _add_job_log(db, job.id, "INFO", f"Incoming file size: {known_size_bytes} bytes")

    return job


def _mark_upload_job_failed(db: Session, job: Job | None, message: str) -> None:
    if job is None:
        return

    job.status = JobStatus.FAILED.value
    job.error_message = message
    job.progress_percent = max(0, min(100, int(job.progress_percent or 0)))
    job.progress_stage = "failed"
    job.progress_message = message[:512]
    job.finished_at = datetime.now(timezone.utc)

    db.add(job)
    db.commit()
    _add_job_log(db, job.id, "ERROR", message)


def _mark_upload_job_succeeded(db: Session, job: Job, media_asset: MediaAsset) -> None:
    job.status = JobStatus.SUCCEEDED.value
    job.output_media_asset_id = media_asset.id
    job.progress_percent = 100
    job.progress_stage = "done"
    job.progress_message = "Upload completed"
    job.finished_at = datetime.now(timezone.utc)

    db.add(job)
    db.commit()
    _add_job_log(db, job.id, "INFO", f"Upload completed: {media_asset.stored_name}")


@router.post(
    "",
    response_model=MediaAssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload local media file",
)
async def upload_media_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MediaAssetResponse:
    rate_limiter.check(
        key=build_rate_limit_key("uploads:create", request),
        limit=settings.rate_limit_upload_per_minute,
        window_seconds=60,
    )

    upload_job: Job | None = None

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required",
        )

    original_name = safe_file_name(file.filename)
    extension = Path(original_name).suffix.lower()

    if not extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File extension is required",
        )

    try:
        kind = detect_kind(extension)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    known_size_bytes = int(file.size) if file.size is not None else None
    upload_job = _create_upload_job(db, current_user, original_name, extension, known_size_bytes)

    try:
        if known_size_bytes is not None:
            assert_can_store_bytes(db, current_user, known_size_bytes)

        upload_dir = build_upload_dir(kind)
        upload_dir.mkdir(parents=True, exist_ok=True)

        stored_name = build_unique_stored_name(upload_dir, original_name)
        target_path = upload_dir / stored_name

        upload_job.progress_percent = 35
        upload_job.progress_stage = "saving"
        upload_job.progress_message = "Saving uploaded file"
        db.add(upload_job)
        db.commit()

        size_bytes, checksum = await save_upload_file(file, target_path)

        try:
            assert_can_store_bytes(db, current_user, size_bytes)
        except HTTPException:
            if target_path.exists():
                target_path.unlink(missing_ok=True)
            raise

        mime_type = guess_mime_type(target_path)

        media_asset = MediaAsset(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            kind=kind,
            original_name=original_name,
            stored_name=stored_name,
            mime_type=mime_type,
            extension=extension.lstrip("."),
            size_bytes=size_bytes,
            duration_sec=None,
            path=str(target_path).replace("\\", "/"),
            checksum_sha256=checksum,
        )

        db.add(media_asset)
        db.commit()
        db.refresh(media_asset)

        increment_storage_used(db, current_user, size_bytes)
        _mark_upload_job_succeeded(db, upload_job, media_asset)

        return build_media_asset_response(media_asset)
    except HTTPException as exc:
        _mark_upload_job_failed(db, upload_job, str(exc.detail))
        raise
    except Exception as exc:
        _mark_upload_job_failed(db, upload_job, str(exc))
        raise
