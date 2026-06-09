from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class ConsentCreate(BaseModel):
    document_type: str = Field(min_length=2, max_length=100)
    document_version: str = Field(min_length=1, max_length=50)
    accepted: bool = True


class ConsentRead(BaseModel):
    id: int
    user_id: int
    document_type: str
    document_version: str
    accepted: bool
    created_at: datetime

    model_config = {'from_attributes': True}
