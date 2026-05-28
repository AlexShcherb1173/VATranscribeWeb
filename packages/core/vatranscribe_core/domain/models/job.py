from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from packages.core.vatranscribe_core.domain.enums import JobStatus, JobType, SourceType


@dataclass(slots=True)
class Job:
    id: UUID
    type: JobType
    status: JobStatus
    source_type: SourceType | None
    user_id: UUID | None
    title: str | None
    input_url: str | None
    input_file_id: UUID | None
    selected_format_id: str | None
    download_audio: bool
    download_video: bool
    transcription_model: str | None
    transcription_language: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
