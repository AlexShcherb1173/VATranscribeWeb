from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from apps.api.app.config import get_settings
from apps.api.app.models import ExportArtifact, Job, JobStatus, MediaAsset, Transcript, User
from apps.api.app.services.quota_service import sync_storage_usage_from_media_assets
from packages.core.vatranscribe_core.storage import resolve_storage_path


@dataclass(slots=True)
class StorageCleanupResult:
    temp_files_deleted: int = 0
    failed_job_files_deleted: int = 0
    export_artifacts_deleted: int = 0
    media_assets_deleted: int = 0
    transcripts_deleted: int = 0
    bytes_deleted: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "temp_files_deleted": self.temp_files_deleted,
            "failed_job_files_deleted": self.failed_job_files_deleted,
            "export_artifacts_deleted": self.export_artifacts_deleted,
            "media_assets_deleted": self.media_assets_deleted,
            "transcripts_deleted": self.transcripts_deleted,
            "bytes_deleted": self.bytes_deleted,
        }


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _file_mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _delete_file(path: Path) -> int:
    try:
        if path.exists() and path.is_file():
            size = path.stat().st_size
            path.unlink(missing_ok=True)
            return size
    except OSError:
        return 0
    return 0


def cleanup_temp_files(*, temp_dir: Path, older_than: datetime, batch_size: int) -> tuple[int, int]:
    deleted = 0
    bytes_deleted = 0

    if not temp_dir.exists():
        return deleted, bytes_deleted

    for path in sorted(temp_dir.rglob("*")):
        if deleted >= batch_size:
            break
        if not path.is_file():
            continue
        try:
            if _file_mtime(path) >= older_than:
                continue
        except OSError:
            continue
        removed = _delete_file(path)
        if removed:
            deleted += 1
            bytes_deleted += removed

    return deleted, bytes_deleted


def cleanup_expired_export_artifacts(db: Session, *, older_than: datetime, batch_size: int) -> tuple[int, int, set[str]]:
    deleted = 0
    bytes_deleted = 0
    affected_user_ids: set[str] = set()

    artifacts = db.scalars(
        select(ExportArtifact)
        .options(selectinload(ExportArtifact.transcript).selectinload(Transcript.media_asset))
        .where(ExportArtifact.created_at < older_than)
        .limit(batch_size)
    ).all()

    for artifact in artifacts:
        media_asset = artifact.transcript.media_asset if artifact.transcript else None
        if media_asset and media_asset.user_id:
            affected_user_ids.add(str(media_asset.user_id))
        bytes_deleted += _delete_file(resolve_storage_path(artifact.path))
        db.delete(artifact)
        deleted += 1

    db.commit()
    return deleted, bytes_deleted, affected_user_ids


def cleanup_expired_transcripts(db: Session, *, older_than: datetime, batch_size: int) -> tuple[int, int, set[str]]:
    deleted = 0
    bytes_deleted = 0
    affected_user_ids: set[str] = set()

    transcripts = db.scalars(
        select(Transcript)
        .options(selectinload(Transcript.export_artifacts), selectinload(Transcript.media_asset))
        .where(Transcript.created_at < older_than)
        .limit(batch_size)
    ).all()

    for transcript in transcripts:
        if transcript.media_asset and transcript.media_asset.user_id:
            affected_user_ids.add(str(transcript.media_asset.user_id))
        for artifact in list(transcript.export_artifacts):
            bytes_deleted += _delete_file(resolve_storage_path(artifact.path))
        db.delete(transcript)
        deleted += 1

    db.commit()
    return deleted, bytes_deleted, affected_user_ids


def _has_active_job(db: Session, media_asset: MediaAsset) -> bool:
    active = {JobStatus.PENDING.value, JobStatus.RUNNING.value}
    stmt = select(Job.id).where(
        Job.output_media_asset_id == media_asset.id,
        Job.status.in_(active),
    ).limit(1)
    return db.scalar(stmt) is not None


def cleanup_expired_media_assets(db: Session, *, older_than: datetime, batch_size: int) -> tuple[int, int, set[str]]:
    deleted = 0
    bytes_deleted = 0
    affected_user_ids: set[str] = set()

    media_assets = db.scalars(
        select(MediaAsset)
        .options(selectinload(MediaAsset.transcripts).selectinload(Transcript.export_artifacts))
        .where(MediaAsset.created_at < older_than)
        .limit(batch_size)
    ).all()

    for media_asset in media_assets:
        if _has_active_job(db, media_asset):
            continue
        if media_asset.user_id:
            affected_user_ids.add(str(media_asset.user_id))
        for transcript in list(media_asset.transcripts):
            for artifact in list(transcript.export_artifacts):
                bytes_deleted += _delete_file(resolve_storage_path(artifact.path))
        bytes_deleted += _delete_file(resolve_storage_path(media_asset.path))
        db.delete(media_asset)
        deleted += 1

    db.commit()
    return deleted, bytes_deleted, affected_user_ids


def cleanup_failed_job_files(db: Session, *, older_than: datetime, batch_size: int) -> tuple[int, int, set[str]]:
    deleted = 0
    bytes_deleted = 0
    affected_user_ids: set[str] = set()

    failed_jobs = db.scalars(
        select(Job)
        .options(selectinload(Job.output_media_asset))
        .where(Job.status == JobStatus.FAILED.value, Job.finished_at < older_than)
        .limit(batch_size)
    ).all()

    for job in failed_jobs:
        media_asset = job.output_media_asset
        if media_asset is None:
            continue
        if media_asset.user_id:
            affected_user_ids.add(str(media_asset.user_id))
        bytes_deleted += _delete_file(resolve_storage_path(media_asset.path))
        db.delete(media_asset)
        deleted += 1

    db.commit()
    return deleted, bytes_deleted, affected_user_ids


def cleanup_storage_retention(db: Session) -> dict[str, int]:
    settings = get_settings()
    now = _utcnow()
    result = StorageCleanupResult()
    affected_user_ids: set[str] = set()

    count, bytes_deleted = cleanup_temp_files(
        temp_dir=settings.temp_dir,
        older_than=now - timedelta(hours=settings.temp_file_retention_hours),
        batch_size=settings.cleanup_batch_size,
    )
    result.temp_files_deleted += count
    result.bytes_deleted += bytes_deleted

    count, bytes_deleted, users = cleanup_failed_job_files(
        db,
        older_than=now - timedelta(days=settings.failed_job_file_retention_days),
        batch_size=settings.cleanup_batch_size,
    )
    result.failed_job_files_deleted += count
    result.bytes_deleted += bytes_deleted
    affected_user_ids.update(users)

    count, bytes_deleted, users = cleanup_expired_export_artifacts(
        db,
        older_than=now - timedelta(days=settings.export_artifact_retention_days),
        batch_size=settings.cleanup_batch_size,
    )
    result.export_artifacts_deleted += count
    result.bytes_deleted += bytes_deleted
    affected_user_ids.update(users)

    count, bytes_deleted, users = cleanup_expired_transcripts(
        db,
        older_than=now - timedelta(days=settings.transcript_retention_days),
        batch_size=settings.cleanup_batch_size,
    )
    result.transcripts_deleted += count
    result.bytes_deleted += bytes_deleted
    affected_user_ids.update(users)

    count, bytes_deleted, users = cleanup_expired_media_assets(
        db,
        older_than=now - timedelta(days=settings.media_asset_retention_days),
        batch_size=settings.cleanup_batch_size,
    )
    result.media_assets_deleted += count
    result.bytes_deleted += bytes_deleted
    affected_user_ids.update(users)

    for user_id in affected_user_ids:
        user = db.get(User, user_id)
        if user is not None:
            sync_storage_usage_from_media_assets(db, user)

    return result.as_dict()
