from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from apps.api.app.celery_client import celery_client
from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import (
    Job,
    JobLog,
    JobStatus,
    JobType,
    MediaAsset,
    SourceType,
    Transcript,
    User,
)
from apps.api.app.schemas import JobResponse
from apps.api.app.services.quota_service import (
    assert_can_create_job,
    assert_can_use_transcription_seconds,
    estimate_media_duration_seconds,
    increment_jobs_used,
)

router = APIRouter(prefix="/transcriptions")


class TranscriptionJobCreateRequest(BaseModel):
    """Request payload for creating a transcription job.

    Kept local to this router so newly introduced frontend fields can be accepted
    even when older shared schema modules are stale during development.
    """

    model_config = ConfigDict(extra="ignore")

    media_asset_id: str
    model_name: str | None = Field(default="medium")
    language: str | None = None
    export_formats: list[str] = Field(default_factory=lambda: ["txt", "srt", "vtt", "json"])
    transcription_scheme: str | None = None
    content_profile: str | None = None
    audio_profile: str | None = None
    generate_summary: bool | None = None
    generate_content_pack: bool | None = None




def _normalize_transcription_language(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip().lower()

    if normalized in {"", "auto", "detect", "auto-detect", "autodetect", "none", "null"}:
        return None

    return normalized


def _source_file_name(transcript: Transcript) -> str | None:
    media_asset = transcript.media_asset

    if media_asset is None:
        return None

    return (
        media_asset.original_name
        or media_asset.stored_name
        or Path(media_asset.path or "").name
        or None
    )


def _transcript_payload(transcript: Transcript) -> dict[str, Any]:
    media_asset = transcript.media_asset
    source_file_name = _source_file_name(transcript)

    return {
        "id": transcript.id,
        "job_id": transcript.job_id,
        "media_asset_id": transcript.media_asset_id,
        "media_asset": {
            "id": media_asset.id,
            "kind": media_asset.kind,
            "original_name": media_asset.original_name,
            "stored_name": media_asset.stored_name,
            "mime_type": media_asset.mime_type,
            "extension": media_asset.extension,
            "size_bytes": media_asset.size_bytes,
            "duration_sec": media_asset.duration_sec,
            "path": media_asset.path,
            "checksum_sha256": media_asset.checksum_sha256,
            "created_at": media_asset.created_at,
            "download_url": f"/media-assets/{media_asset.id}/download",
        } if media_asset is not None else None,
        "source_file_name": source_file_name,
        "display_name": source_file_name or getattr(transcript.job, "title", None) or transcript.id,
        "language": transcript.language,
        "model_name": transcript.model_name,
        "engine": transcript.engine,
        "full_text": transcript.full_text,
        "duration_sec": getattr(transcript, "duration_sec", None),
        "segments_count": getattr(transcript, "segments_count", None),
        "coverage_sec": getattr(transcript, "coverage_sec", None),
        "coverage_ratio": getattr(transcript, "coverage_ratio", None),
        "quality_status": getattr(transcript, "quality_status", None),
        "quality_warning": getattr(transcript, "quality_warning", None),
        "created_at": transcript.created_at,
        "segments": [
            {
                "id": segment.id,
                "transcript_id": segment.transcript_id,
                "start_sec": segment.start_sec,
                "end_sec": segment.end_sec,
                "text": segment.text,
                "speaker_label": segment.speaker_label,
                "confidence": segment.confidence,
                "order_index": segment.order_index,
            }
            for segment in transcript.segments
        ],
        "exports": [
            {
                "id": artifact.id,
                "transcript_id": artifact.transcript_id,
                "format": artifact.format,
                "path": artifact.path,
                "size_bytes": artifact.size_bytes,
                "created_at": artifact.created_at,
                "download_url": f"/transcripts/export-artifacts/{artifact.id}/download",
            }
            for artifact in transcript.export_artifacts
        ],
    }


@router.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and enqueue transcription job",
)
def create_transcription_job(
    payload: TranscriptionJobCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobResponse:
    stmt = select(MediaAsset).where(
        MediaAsset.id == payload.media_asset_id,
        MediaAsset.user_id == current_user.id,
    )
    media_asset = db.scalar(stmt)

    if media_asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media asset '{payload.media_asset_id}' not found",
        )

    assert_can_create_job(db, current_user, jobs_to_add=1)
    assert_can_use_transcription_seconds(
        db,
        current_user,
        seconds_to_add=estimate_media_duration_seconds(media_asset),
    )

    source_name = (
        media_asset.original_name
        or media_asset.stored_name
        or Path(media_asset.path or "").name
        or media_asset.id
    )

    job = Job(
        user_id=current_user.id,
        type=JobType.TRANSCRIBE.value,
        status=JobStatus.QUEUED.value,
        source_type=SourceType.LOCAL_FILE.value,
        title=f"Transcribe {source_name}",
        transcription_media_asset_id=media_asset.id,
        transcription_model=payload.model_name,
        transcription_language=_normalize_transcription_language(payload.language),
        transcription_profile=(
            getattr(payload, "audio_profile", None)
            or getattr(payload, "content_profile", None)
            or getattr(payload, "transcription_scheme", None)
        ),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    increment_jobs_used(db, current_user, 1)

    db.add(JobLog(job_id=job.id, level="INFO", message="Transcription job created"))
    db.add(JobLog(job_id=job.id, level="INFO", message="Transcription job enqueued"))
    db.commit()

    celery_client.send_task("vatranscribe.jobs.execute", args=[job.id])

    return job


@router.get(
    "/{transcript_id}",
    response_model=None,
    summary="Get transcript by id",
)
def get_transcript(
    transcript_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    stmt = (
        select(Transcript)
        .join(MediaAsset, Transcript.media_asset_id == MediaAsset.id)
        .options(
            selectinload(Transcript.media_asset),
            selectinload(Transcript.job),
            selectinload(Transcript.segments),
            selectinload(Transcript.export_artifacts),
        )
        .where(
            Transcript.id == transcript_id,
            MediaAsset.user_id == current_user.id,
        )
    )
    transcript = db.scalar(stmt)

    if transcript is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcript '{transcript_id}' not found",
        )

    return _transcript_payload(transcript)
