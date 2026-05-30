from __future__ import annotations

from fastapi import APIRouter

from apps.api.app.schemas.consent import ConsentCreate
from apps.api.app.services.consent_service import consent_service

router = APIRouter(prefix='/consents', tags=['consents'])


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
