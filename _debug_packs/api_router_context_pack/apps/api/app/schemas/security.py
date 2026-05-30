from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class SecurityEventRead(BaseModel):
    id: int
    user_id: int | None = None
    event_type: str
    severity: str
    created_at: datetime

    model_config = {'from_attributes': True}
