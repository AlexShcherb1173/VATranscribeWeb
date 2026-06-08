from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.celery_client import celery_client
from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import Job, JobLog, JobStatus, JobType, SourceType, User
from apps.api.app.schemas import (
    DownloadAnalyzeRequest,
    DownloadAnalyzeResponse,
    DownloadJobCreateRequest,
    JobResponse,
)
from apps.api.app.services.quota_service import assert_can_create_job, increment_jobs_used
from apps.api.app.services.youtube_cookies_service import (
    create_temp_youtube_cookies_file_for_user,
    delete_temp_youtube_cookies_file,
)
from packages.core.vatranscribe_core.download_engine import analyze_url

router = APIRouter(prefix="/downloads")

ALLOWED_DOWNLOAD_MODES = {
    "audio_mp3",
    "video_mp4_compatible",
    "video_mp4_fast",
    "selected_original",
    "best_available",
}


def _normalize_download_error(exc: Exception) -> str:
    message = str(exc)
    normalized = message.lower()

    if "video unavailable" in normalized or "this video is unavailable" in normalized:
        return (
            "Видео недоступно. Возможные причины: ролик удалён, приватный, "
            "ограничен регионом/возрастом или недоступен для текущего аккаунта. "
            f"Оригинальная ошибка yt-dlp: {message}"
        )

    if "requested format is not available" in normalized or "format is not available" in normalized:
        return (
            "Выбранный формат недоступен для этого видео. "
            "Попробуй режим best_available или другой формат. "
            f"Оригинальная ошибка yt-dlp: {message}"
        )

    if (
        "sign in to confirm" in normalized
        or "not a bot" in normalized
        or "use --cookies" in normalized
        or "cookies" in normalized
    ):
        return (
            "YouTube требует авторизацию или cookies. "
            "Загрузи актуальный youtube.txt в Настройки → YouTube cookies. "
            f"Оригинальная ошибка yt-dlp: {message}"
        )

    return f"Failed to analyze URL: {message}"


@router.post(
    "/analyze",
    response_model=DownloadAnalyzeResponse,
    summary="Analyze URL formats",
)
def analyze_download_url(
    payload: DownloadAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DownloadAnalyzeResponse:
    cookies_file = create_temp_youtube_cookies_file_for_user(
        db,
        user_id=current_user.id,
        job_id=f"analyze-{current_user.id}",
    )

    try:
        result = analyze_url(payload.url, cookies_file=cookies_file)
        return DownloadAnalyzeResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_normalize_download_error(exc),
        ) from exc
    finally:
        delete_temp_youtube_cookies_file(cookies_file)


@router.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and enqueue download job",
)
def create_download_job(
    payload: DownloadJobCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    assert_can_create_job(db, current_user, jobs_to_add=1)

    download_mode = payload.download_mode.lower().strip()
    requested_format = payload.requested_format.lower().strip().lstrip(".")
    mp4_mode = (payload.mp4_mode or "compatible").lower().strip()

    if download_mode not in ALLOWED_DOWNLOAD_MODES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"download_mode must be one of: {', '.join(sorted(ALLOWED_DOWNLOAD_MODES))}",
        )

    if not requested_format:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="requested_format is required",
        )

    if mp4_mode not in {"fast", "compatible"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="mp4_mode must be 'fast' or 'compatible'",
        )

    if download_mode == "audio_mp3":
        requested_format = "mp3"
        mp4_mode = "compatible"

    if download_mode == "video_mp4_compatible":
        requested_format = "mp4"
        mp4_mode = "compatible"

    if download_mode == "video_mp4_fast":
        requested_format = "mp4"
        mp4_mode = "fast"

    if download_mode == "best_available" and requested_format not in {"mp4", "webm", "mkv", "mp3", "m4a"}:
        requested_format = "mp4"

    if download_mode == "selected_original" and not payload.selected_format_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="selected_format_id is required for selected_original mode",
        )

    selected_video_format_id = payload.selected_video_format_id

    if download_mode == "selected_original":
        selected_video_format_id = payload.selected_format_id

    job = Job(
        user_id=current_user.id,
        type=JobType.DOWNLOAD.value,
        status=JobStatus.QUEUED.value,
        source_type=SourceType.URL.value,
        title=f"Download {payload.requested_file_name}",
        input_url=payload.url.strip(),
        requested_format=requested_format,
        requested_file_name=payload.requested_file_name,
        mp4_mode=download_mode,
        selected_video_format_id=selected_video_format_id,
        selected_audio_format_id=payload.selected_audio_format_id,
        download_audio=download_mode == "audio_mp3",
        download_video=download_mode != "audio_mp3",
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    increment_jobs_used(db, current_user, 1)

    db.add(JobLog(job_id=job.id, level="INFO", message=f"Download job created: mode={download_mode}"))
    db.add(JobLog(job_id=job.id, level="INFO", message=f"Requested format: {requested_format}"))

    if selected_video_format_id:
        db.add(JobLog(job_id=job.id, level="INFO", message=f"Selected video format: {selected_video_format_id}"))

    if payload.selected_audio_format_id:
        db.add(JobLog(job_id=job.id, level="INFO", message=f"Selected audio format: {payload.selected_audio_format_id}"))

    db.add(JobLog(job_id=job.id, level="INFO", message="Download job enqueued"))
    db.commit()

    celery_client.send_task("vatranscribe.jobs.execute", args=[job.id])

    return job
