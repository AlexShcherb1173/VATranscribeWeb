from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from packages.core.vatranscribe_core.domain.enums import OutputFormat


@dataclass(slots=True)
class ExportArtifact:
    id: UUID
    transcript_id: UUID
    format: OutputFormat | str
    path: str
    size_bytes: int
    created_at: datetime
