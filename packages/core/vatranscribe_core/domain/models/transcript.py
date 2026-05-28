from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from packages.core.vatranscribe_core.domain.enums import TranscriptionEngine


@dataclass(slots=True)
class Transcript:
    id: UUID
    job_id: UUID
    media_asset_id: UUID
    language: str
    model_name: str
    engine: TranscriptionEngine | str
    full_text: str
    created_at: datetime
