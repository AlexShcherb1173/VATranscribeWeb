from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Segment:
    id: UUID
    transcript_id: UUID
    start_sec: int
    end_sec: int
    text: str
    speaker_label: str | None
    confidence: str | None
    order_index: int
