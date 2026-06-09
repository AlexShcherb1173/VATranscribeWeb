from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.models import ExportArtifact, MediaAsset, Transcript, UsageSnapshot, User, UserQuota
from apps.api.app.services.account_bootstrap import ensure_user_quota


class QuotaExceededError(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


@dataclass(slots=True)
class QuotaSnapshot:
    storage_bytes_used: int
    transcription_seconds_used: int
    jobs_count_used: int
    storage_bytes_limit: int
    transcription_seconds_limit: int
    jobs_count_limit: int


def _today_label() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_or_create_quota(db: Session, user: User) -> UserQuota:
    return ensure_user_quota(db, user)


def record_usage_snapshot(
    db: Session,
    user: User,
    quota: UserQuota,
    label: str | None = None,
) -> UsageSnapshot:
    snapshot_label = label or _today_label()

    snapshot = db.scalar(
        select(UsageSnapshot).where(
            UsageSnapshot.user_id == str(user.id),
            UsageSnapshot.label == snapshot_label,
        )
    )

    if snapshot is None:
        snapshot = UsageSnapshot(
            id=str(uuid.uuid4()),
            user_id=str(user.id),
            label=snapshot_label,
            storage_bytes_used=quota.storage_bytes_used,
            transcription_seconds_used=quota.transcription_seconds_used,
            jobs_count_used=quota.jobs_count_used,
        )
        db.add(snapshot)
    else:
        snapshot.storage_bytes_used = quota.storage_bytes_used
        snapshot.transcription_seconds_used = quota.transcription_seconds_used
        snapshot.jobs_count_used = quota.jobs_count_used
        db.add(snapshot)

    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_quota_snapshot(db: Session, user: User) -> QuotaSnapshot:
    quota = get_or_create_quota(db, user)
    return QuotaSnapshot(
        storage_bytes_used=quota.storage_bytes_used,
        transcription_seconds_used=quota.transcription_seconds_used,
        jobs_count_used=quota.jobs_count_used,
        storage_bytes_limit=quota.storage_bytes_limit,
        transcription_seconds_limit=quota.transcription_seconds_limit,
        jobs_count_limit=quota.jobs_count_limit,
    )


def assert_can_create_job(db: Session, user: User, jobs_to_add: int = 1) -> None:
    quota = get_or_create_quota(db, user)

    if quota.jobs_count_used + jobs_to_add > quota.jobs_count_limit:
        raise QuotaExceededError("Quota exceeded: jobs limit reached")


def assert_can_store_bytes(db: Session, user: User, bytes_to_add: int) -> None:
    quota = get_or_create_quota(db, user)

    if quota.storage_bytes_used + max(bytes_to_add, 0) > quota.storage_bytes_limit:
        raise QuotaExceededError("Quota exceeded: storage limit reached")


def assert_can_use_transcription_seconds(
    db: Session,
    user: User,
    seconds_to_add: int,
) -> None:
    quota = get_or_create_quota(db, user)

    if quota.transcription_seconds_used + max(seconds_to_add, 0) > quota.transcription_seconds_limit:
        raise QuotaExceededError("Quota exceeded: transcription seconds limit reached")


def increment_jobs_used(db: Session, user: User, amount: int = 1) -> UserQuota:
    quota = get_or_create_quota(db, user)
    quota.jobs_count_used += max(amount, 0)
    db.add(quota)
    db.commit()
    db.refresh(quota)
    record_usage_snapshot(db, user, quota)
    return quota


def increment_storage_used(db: Session, user: User, amount: int) -> UserQuota:
    quota = get_or_create_quota(db, user)
    quota.storage_bytes_used += max(amount, 0)
    db.add(quota)
    db.commit()
    db.refresh(quota)
    record_usage_snapshot(db, user, quota)
    return quota


def decrement_storage_used(db: Session, user: User, amount: int) -> UserQuota:
    quota = get_or_create_quota(db, user)
    quota.storage_bytes_used = max(0, quota.storage_bytes_used - max(amount, 0))
    db.add(quota)
    db.commit()
    db.refresh(quota)
    record_usage_snapshot(db, user, quota)
    return quota


def increment_transcription_seconds_used(
    db: Session,
    user: User,
    amount: int,
) -> UserQuota:
    quota = get_or_create_quota(db, user)
    quota.transcription_seconds_used += max(amount, 0)
    db.add(quota)
    db.commit()
    db.refresh(quota)
    record_usage_snapshot(db, user, quota)
    return quota


def calculate_storage_usage_bytes(db: Session, user: User) -> int:
    media_total = sum(
        int(value or 0)
        for value in db.scalars(
            select(MediaAsset.size_bytes).where(MediaAsset.user_id == str(user.id))
        ).all()
    )

    export_total = sum(
        int(value or 0)
        for value in db.scalars(
            select(ExportArtifact.size_bytes)
            .join(Transcript, ExportArtifact.transcript_id == Transcript.id)
            .join(MediaAsset, Transcript.media_asset_id == MediaAsset.id)
            .where(MediaAsset.user_id == str(user.id))
        ).all()
    )

    return media_total + export_total


def sync_storage_usage_from_media_assets(db: Session, user: User) -> UserQuota:
    quota = get_or_create_quota(db, user)
    quota.storage_bytes_used = calculate_storage_usage_bytes(db, user)
    db.add(quota)
    db.commit()
    db.refresh(quota)
    record_usage_snapshot(db, user, quota)
    return quota


def estimate_media_duration_seconds(media_asset: MediaAsset) -> int:
    return max(int(media_asset.duration_sec or 0), 0)