from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.celery_client import celery_client
from apps.api.app.config import settings
from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import Job, JobLog, JobStatus, MediaAsset, User
from apps.api.app.schemas import (
    JobActionResponse,
    JobCreateRequest,
    JobLogResponse,
    JobResponse,
)
from apps.api.app.security_foundation.rate_limits import build_rate_limit_key, rate_limiter
from apps.api.app.services.quota_service import assert_can_create_job, increment_jobs_used, sync_storage_usage_from_media_assets
from apps.api.app.services.access_control import get_user_media_asset_or_404
from packages.core.vatranscribe_core.storage import resolve_storage_path
from packages.core.vatranscribe_core.url_guard import UnsafeUrlError, validate_external_url

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def _validate_user_url_or_422(url: str) -> str:
    try:
        return validate_external_url(url)
    except UnsafeUrlError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsafe or unsupported external URL: {exc}",
        ) from exc


def _normalize_transcription_language(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip().lower()

    if normalized in {"", "auto", "detect", "auto-detect", "autodetect", "none", "null"}:
        return None

    return normalized


def _get_job_or_404(job_id: str, db: Session, current_user: User) -> Job:
    stmt = select(Job).where(
        Job.id == job_id,
        Job.user_id == current_user.id,
    )
    job = db.scalar(stmt)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    return job


def _add_log(db: Session, job_id: str, level: str, message: str) -> None:
    now = _utcnow()

    db.add(JobLog(job_id=job_id, level=level, message=message))

    job = db.get(Job, job_id)
    if job is not None:
        if hasattr(job, "heartbeat_at"):
            job.heartbeat_at = now
        if hasattr(job, "last_log_at"):
            job.last_log_at = now
        if hasattr(job, "last_log_message"):
            job.last_log_message = message
        db.add(job)

    db.commit()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


ACTIVE_JOB_STATUSES = {
    JobStatus.PENDING.value,
    JobStatus.QUEUED.value,
    JobStatus.RUNNING.value,
    "processing",
    "started",
    "in_progress",
}


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    utc_value = _as_utc(value)
    return utc_value.isoformat() if utc_value else None


def _is_stale_job(job: Job) -> bool:
    if (job.status or "").lower() not in ACTIVE_JOB_STATUSES:
        return False

    heartbeat_at = _as_utc(getattr(job, "heartbeat_at", None))
    last_log_at = _as_utc(getattr(job, "last_log_at", None))
    updated_at = _as_utc(getattr(job, "updated_at", None))
    reference = heartbeat_at or last_log_at or updated_at or _as_utc(job.started_at)

    if reference is None:
        return False

    stale_after = timedelta(minutes=5)

    if (getattr(job, "transcription_profile", None) or "").lower() == "lyrics_music":
        stale_after = timedelta(minutes=30)

    return _utcnow() - reference > stale_after


def _serialize_media_asset(media_asset: MediaAsset | None) -> dict | None:
    if media_asset is None:
        return None

    return {
        "id": media_asset.id,
        "kind": media_asset.kind,
        "original_name": media_asset.original_name,
        "stored_name": media_asset.stored_name,
        "mime_type": media_asset.mime_type,
        "extension": media_asset.extension,
        "size_bytes": media_asset.size_bytes,
        "duration_sec": media_asset.duration_sec,
        "checksum_sha256": media_asset.checksum_sha256,
        "created_at": _iso(media_asset.created_at),
        "download_url": f"/api/v1/media-assets/{media_asset.id}/download",
    }


def _latest_log(job: Job) -> JobLog | None:
    logs = list(getattr(job, "logs", []) or [])
    if not logs:
        return None

    return max(logs, key=lambda item: item.created_at)


def _serialize_job(job: Job) -> dict:
    latest_log = _latest_log(job)
    last_log_at = getattr(job, "last_log_at", None) or (latest_log.created_at if latest_log else None)
    last_log_message = (
        getattr(job, "last_log_message", None)
        or (latest_log.message if latest_log else None)
        or getattr(job, "progress_message", None)
    )
    heartbeat_at = getattr(job, "heartbeat_at", None) or last_log_at or getattr(job, "started_at", None)

    return {
        "id": job.id,
        "type": job.type,
        "status": job.status,
        "source_type": job.source_type,
        "title": job.title,
        "input_url": job.input_url,
        "requested_format": job.requested_format,
        "requested_file_name": job.requested_file_name,
        "mp4_mode": job.mp4_mode,
        "output_media_asset_id": job.output_media_asset_id,
        "output_media_asset": _serialize_media_asset(job.output_media_asset),
        "transcription_media_asset": _serialize_media_asset(job.transcription_media_asset),
        "selected_video_format_id": job.selected_video_format_id,
        "selected_audio_format_id": job.selected_audio_format_id,
        "transcription_media_asset_id": job.transcription_media_asset_id,
        "download_audio": job.download_audio,
        "download_video": job.download_video,
        "transcription_model": job.transcription_model,
        "transcription_language": job.transcription_language,
        "transcription_profile": getattr(job, "transcription_profile", None),
        "error_message": job.error_message,
        "progress_percent": job.progress_percent,
        "progress_stage": job.progress_stage,
        "progress_message": job.progress_message,
        "heartbeat_at": _iso(heartbeat_at),
        "last_log_at": _iso(last_log_at),
        "last_log_message": last_log_message,
        "current_step": job.progress_message or job.progress_stage or last_log_message,
        "is_stale": _is_stale_job(job),
        "created_at": _iso(job.created_at),
        "started_at": _iso(job.started_at),
        "finished_at": _iso(job.finished_at),
    }


def _remove_media_file_safely(media_asset: MediaAsset | None) -> None:
    if media_asset is None or not media_asset.path:
        return

    path = resolve_storage_path(media_asset.path)

    try:
        if path.exists() and path.is_file():
            path.unlink(missing_ok=True)
    except OSError:
        pass


def _enqueue_existing_job(db: Session, job: Job, message: str) -> JobActionResponse:
    now = _utcnow()
    job.status = JobStatus.QUEUED.value
    job.error_message = None
    job.started_at = None
    job.finished_at = None
    if hasattr(job, "heartbeat_at"):
        job.heartbeat_at = now
    if hasattr(job, "last_log_at"):
        job.last_log_at = now
    if hasattr(job, "last_log_message"):
        job.last_log_message = message

    db.add(job)
    db.commit()
    db.refresh(job)

    _add_log(db, job.id, "INFO", message)

    celery_client.send_task("vatranscribe.jobs.execute", args=[job.id])

    return JobActionResponse(
        ok=True,
        job_id=job.id,
        status=job.status,
        detail=message,
    )


@router.get("", response_model=None, summary="List jobs")
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    stmt = (
        select(Job)
        .where(Job.user_id == current_user.id)
        .order_by(Job.created_at.desc())
    )

    jobs = db.scalars(stmt).unique().all()
    return [_serialize_job(job) for job in jobs]


@router.get("/{job_id}", response_model=None, summary="Get job by id")
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return _serialize_job(_get_job_or_404(job_id, db, current_user))


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create generic job",
)
def create_job(
    payload: JobCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Job:
    if payload.input_url:
        rate_limiter.check(
            key=build_rate_limit_key("jobs:url_create", request),
            limit=settings.rate_limit_download_per_minute,
            window_seconds=60,
        )

    assert_can_create_job(db, current_user, jobs_to_add=1)

    if payload.transcription_media_asset_id:
        get_user_media_asset_or_404(
            db=db,
            current_user=current_user,
            media_asset_id=payload.transcription_media_asset_id,
        )

    input_url = None
    if payload.input_url:
        input_url = _validate_user_url_or_422(payload.input_url)

    job = Job(
        user_id=current_user.id,
        type=payload.type,
        status=JobStatus.PENDING.value,
        source_type=payload.source_type,
        title=payload.title,
        input_url=input_url,
        requested_format=payload.requested_format,
        requested_file_name=payload.requested_file_name,
        mp4_mode=payload.mp4_mode,
        selected_video_format_id=payload.selected_video_format_id,
        selected_audio_format_id=payload.selected_audio_format_id,
        transcription_media_asset_id=payload.transcription_media_asset_id,
        download_audio=payload.download_audio,
        download_video=payload.download_video,
        transcription_model=payload.transcription_model,
        transcription_language=_normalize_transcription_language(payload.transcription_language),
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    increment_jobs_used(db, current_user, 1)

    db.add(JobLog(job_id=job.id, level="INFO", message="Job created"))
    db.commit()

    return job


@router.get(
    "/{job_id}/logs",
    response_model=list[JobLogResponse],
    summary="Get job logs",
)
def get_job_logs(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[JobLog]:
    _get_job_or_404(job_id, db, current_user)

    stmt = (
        select(JobLog)
        .where(JobLog.job_id == job_id)
        .order_by(JobLog.created_at.asc())
    )

    logs = db.scalars(stmt).all()
    return list(logs)


@router.post(
    "/{job_id}/enqueue",
    response_model=JobActionResponse,
    summary="Enqueue job",
)
def enqueue_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobActionResponse:
    job = _get_job_or_404(job_id, db, current_user)

    if job.status == JobStatus.RUNNING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job is already running",
        )

    if job.status == JobStatus.CANCELED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Canceled job cannot be enqueued",
        )

    return _enqueue_existing_job(db, job, "Job enqueued")


@router.post(
    "/{job_id}/retry",
    response_model=JobActionResponse,
    summary="Retry job",
)
def retry_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobActionResponse:
    job = _get_job_or_404(job_id, db, current_user)

    if job.status not in {
        JobStatus.FAILED.value,
        JobStatus.CANCELED.value,
        JobStatus.SUCCEEDED.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only failed, canceled, or succeeded jobs can be retried",
        )

    return _enqueue_existing_job(db, job, "Job retried and enqueued")


@router.post(
    "/{job_id}/restart",
    response_model=JobActionResponse,
    summary="Restart job",
)
def restart_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobActionResponse:
    """
    Frontend-compatible alias for retry.
    """
    return retry_job(job_id=job_id, db=db, current_user=current_user)


@router.post(
    "/{job_id}/cancel",
    response_model=JobActionResponse,
    summary="Cancel job",
)
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobActionResponse:
    job = _get_job_or_404(job_id, db, current_user)

    if job.status in {
        JobStatus.SUCCEEDED.value,
        JobStatus.FAILED.value,
        JobStatus.CANCELED.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Completed or canceled job cannot be canceled",
        )

    now = _utcnow()
    job.status = JobStatus.CANCELED.value
    if hasattr(job, "heartbeat_at"):
        job.heartbeat_at = now
    if hasattr(job, "last_log_at"):
        job.last_log_at = now
    if hasattr(job, "last_log_message"):
        job.last_log_message = "Job canceled"

    db.add(job)
    db.commit()
    db.refresh(job)

    _add_log(db, job.id, "WARNING", "Job canceled")

    return JobActionResponse(
        ok=True,
        job_id=job.id,
        status=job.status,
        detail="Job canceled",
    )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete job",
)
def delete_job(
    job_id: str,
    delete_media: bool = Query(
        default=False,
        description="Also delete output media file created by this job.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str | bool]:
    job = _get_job_or_404(job_id, db, current_user)

    if job.status == JobStatus.RUNNING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Running job cannot be deleted. Cancel it first.",
        )

    media_asset_to_delete = job.output_media_asset if delete_media else None
    deleted_media_asset_id = media_asset_to_delete.id if media_asset_to_delete else None

    db.delete(job)
    db.commit()

    if media_asset_to_delete is not None:
        _remove_media_file_safely(media_asset_to_delete)
        db.delete(media_asset_to_delete)
        db.commit()
        sync_storage_usage_from_media_assets(db, current_user)

    return {
        "ok": True,
        "job_id": job_id,
        "deleted_media": bool(deleted_media_asset_id),
        "deleted_media_asset_id": deleted_media_asset_id or "",
    }


@router.post(
    "/{job_id}/stop",
    response_model=JobActionResponse,
    summary="Stop job",
)
def stop_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobActionResponse:
    """
    Frontend-compatible alias for cancel.
    """
    return cancel_job(job_id=job_id, db=db, current_user=current_user)



