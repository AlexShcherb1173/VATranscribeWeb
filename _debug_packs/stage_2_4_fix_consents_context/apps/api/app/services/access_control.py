from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from apps.api.app.models import ExportArtifact, Job, MediaAsset, Transcript, User


def not_found(entity: str, entity_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{entity} '{entity_id}' not found",
    )


def get_user_job_or_404(
    db: Session,
    current_user: User,
    job_id: str,
) -> Job:
    stmt = select(Job).where(
        Job.id == job_id,
        Job.user_id == current_user.id,
    )
    item = db.scalar(stmt)

    if item is None:
        raise not_found('Job', job_id)

    return item


def get_user_media_asset_or_404(
    db: Session,
    current_user: User,
    media_asset_id: str,
) -> MediaAsset:
    stmt = select(MediaAsset).where(
        MediaAsset.id == media_asset_id,
        MediaAsset.user_id == current_user.id,
    )
    item = db.scalar(stmt)

    if item is None:
        raise not_found('Media asset', media_asset_id)

    return item


def get_user_transcript_or_404(
    db: Session,
    current_user: User,
    transcript_id: str,
) -> Transcript:
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
    item = db.scalar(stmt)

    if item is None:
        raise not_found('Transcript', transcript_id)

    return item


def get_user_export_artifact_or_404(
    db: Session,
    current_user: User,
    artifact_id: str,
) -> ExportArtifact:
    stmt = (
        select(ExportArtifact)
        .join(Transcript, ExportArtifact.transcript_id == Transcript.id)
        .join(MediaAsset, Transcript.media_asset_id == MediaAsset.id)
        .options(
            selectinload(ExportArtifact.transcript).selectinload(Transcript.media_asset),
        )
        .where(
            ExportArtifact.id == artifact_id,
            MediaAsset.user_id == current_user.id,
        )
    )
    item = db.scalar(stmt)

    if item is None:
        raise not_found('Export artifact', artifact_id)

    return item
