from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class PrivacyRequestCreate(BaseModel):
    request_type: str = Field(pattern='^(export|delete_account|delete_files|revoke_consent)$')
    comment: str | None = None


class PrivacyRequestRead(BaseModel):
    id: int
    user_id: int
    request_type: str
    status: str
    created_at: datetime
    processed_at: datetime | None = None

    model_config = {'from_attributes': True}
