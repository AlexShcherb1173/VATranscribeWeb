from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.app.database import Base


class JobType(str, Enum):
    UPLOAD = "upload"
    DOWNLOAD = "download"
    TRANSCRIBE = "transcribe"
    COMBINED = "combined"
    EXPORT = "export"


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class SourceType(str, Enum):
    URL = "url"
    UPLOAD = "upload"
    LOCAL_FILE = "local_file"


class MediaKind(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    profile: Mapped["UserProfile | None"] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
    )
    quota: Mapped["UserQuota | None"] = relationship(
        "UserQuota",
        back_populates="user",
        uselist=False,
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Subscription.created_at.desc()",
    )
    usage_snapshots: Mapped[list["UsageSnapshot"]] = relationship(
        "UsageSnapshot",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="UsageSnapshot.created_at.asc()",
    )

    media_assets: Mapped[list["MediaAsset"]] = relationship(
        "MediaAsset",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="MediaAsset.user_id",
    )
    jobs: Mapped[list["Job"]] = relationship(
        "Job",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Job.user_id",
    )


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    price_monthly: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(16), nullable=False, default="USD")
    storage_bytes_limit: Mapped[int] = mapped_column(BigInteger, nullable=False)
    transcription_seconds_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    jobs_count_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="plan",
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="subscriptions",
    )
    plan: Mapped["Plan"] = relationship(
        "Plan",
        back_populates="subscriptions",
    )


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    kind: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    extension: Mapped[str | None] = mapped_column(String(32), nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="media_assets",
    )
    jobs_as_output: Mapped[list["Job"]] = relationship(
        "Job",
        back_populates="output_media_asset",
        foreign_keys="Job.output_media_asset_id",
    )
    transcripts: Mapped[list["Transcript"]] = relationship(
        "Transcript",
        back_populates="media_asset",
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        index=True,
        nullable=False,
        default=JobStatus.PENDING.value,
    )
    source_type: Mapped[str | None] = mapped_column(String(32), nullable=True)

    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    output_media_asset_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("media_assets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    input_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    requested_format: Mapped[str | None] = mapped_column(String(16), nullable=True)
    requested_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mp4_mode: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        default="compatible",
    )

    selected_video_format_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    selected_audio_format_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    transcription_media_asset_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("media_assets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    transcription_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transcription_language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    transcription_profile: Mapped[str | None] = mapped_column(String(64), nullable=True)

    download_audio: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    download_video: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    progress_message: Mapped[str | None] = mapped_column(String(512), nullable=True)

    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_log_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_log_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="jobs",
        foreign_keys=[user_id],
    )
    output_media_asset: Mapped["MediaAsset | None"] = relationship(
        "MediaAsset",
        back_populates="jobs_as_output",
        foreign_keys=[output_media_asset_id],
    )
    transcription_media_asset: Mapped["MediaAsset | None"] = relationship(
        "MediaAsset",
        foreign_keys=[transcription_media_asset_id],
    )
    logs: Mapped[list["JobLog"]] = relationship(
        "JobLog",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="JobLog.created_at",
    )
    transcripts: Mapped[list["Transcript"]] = relationship(
        "Transcript",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class JobLog(Base):
    __tablename__ = "job_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="INFO")
    message: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    job: Mapped["Job"] = relationship("Job", back_populates="logs")


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    media_asset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("media_assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    language: Mapped[str] = mapped_column(String(16), nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    engine: Mapped[str] = mapped_column(String(64), nullable=False)
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    segments_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coverage_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coverage_ratio: Mapped[str | None] = mapped_column(String(32), nullable=True)
    quality_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    quality_warning: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    job: Mapped["Job"] = relationship("Job", back_populates="transcripts")
    media_asset: Mapped["MediaAsset"] = relationship("MediaAsset", back_populates="transcripts")
    segments: Mapped[list["TranscriptSegment"]] = relationship(
        "TranscriptSegment",
        back_populates="transcript",
        cascade="all, delete-orphan",
        order_by="TranscriptSegment.order_index",
    )
    export_artifacts: Mapped[list["ExportArtifact"]] = relationship(
        "ExportArtifact",
        back_populates="transcript",
        cascade="all, delete-orphan",
    )


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    transcript_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    end_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    speaker_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(32), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    transcript: Mapped["Transcript"] = relationship("Transcript", back_populates="segments")


class ExportArtifact(Base):
    __tablename__ = "export_artifacts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    transcript_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    format: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    transcript: Mapped["Transcript"] = relationship("Transcript", back_populates="export_artifacts")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")


class UserQuota(Base):
    __tablename__ = "user_quotas"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    storage_bytes_used: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    transcription_seconds_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    jobs_count_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    storage_bytes_limit: Mapped[int] = mapped_column(BigInteger, nullable=False, default=10 * 1024 * 1024 * 1024)
    transcription_seconds_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=36_000)
    jobs_count_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=500)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="quota")


class UsageSnapshot(Base):
    __tablename__ = "usage_snapshots"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(64), nullable=False)

    storage_bytes_used: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    transcription_seconds_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    jobs_count_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="usage_snapshots")