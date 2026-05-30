from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

from apps.api.app.services.consent_service import consent_service


router = APIRouter(prefix='/consents', tags=['consents'])


class ConsentCreate(BaseModel):
    document_type: str = Field(min_length=2, max_length=100)
    document_version: str = Field(min_length=1, max_length=50)
    accepted: bool = True


@router.get('/me')
def list_my_consents() -> dict[str, list[dict]]:
    return {'items': []}


@router.post('')
def create_consent(payload: ConsentCreate) -> dict:
    record = consent_service.build_consent_record(
        user_id=0,
        document_type=payload.document_type,
        document_version=payload.document_version,
        accepted=payload.accepted,
    )
    return {'status': 'accepted', 'consent': record}
