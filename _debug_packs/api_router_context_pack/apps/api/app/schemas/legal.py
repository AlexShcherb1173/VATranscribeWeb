from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class LegalDocumentRead(BaseModel):
    id: int
    document_type: str
    version: str
    title: str
    is_active: bool
    published_at: datetime | None = None

    model_config = {'from_attributes': True}


class LegalDocumentCreate(BaseModel):
    document_type: str = Field(min_length=2, max_length=100)
    version: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=2, max_length=255)
    content: str = Field(min_length=1)
