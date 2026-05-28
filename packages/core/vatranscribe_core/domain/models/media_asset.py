from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from packages.core.vatranscribe_core.domain.enums import MediaKind


@dataclass(slots=True)
class MediaAsset:
    id: UUID
    user_id: UUID | None
    kind: MediaKind
    original_name: str
    stored_name: str
    mime_type: str | None
    extension: str | None
    size_bytes: int
    duration_sec: int | None
    path: str
    checksum_sha256: str | None
    created_at: datetime
