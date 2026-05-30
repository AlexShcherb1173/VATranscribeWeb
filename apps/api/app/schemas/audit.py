from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: int
    actor_user_id: int | None = None
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    created_at: datetime

    model_config = {'from_attributes': True}
