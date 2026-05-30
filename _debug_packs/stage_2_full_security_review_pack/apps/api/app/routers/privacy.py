from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

from apps.api.app.services.privacy_request_service import privacy_request_service


router = APIRouter(prefix='/privacy', tags=['privacy'])


class PrivacyRequestCreate(BaseModel):
    request_type: str = Field(pattern='^(export|delete_account|delete_files|revoke_consent)$')
    comment: str | None = None


@router.get('/me')
def get_my_privacy_overview() -> dict:
    return {'status': 'ok', 'requests': []}


@router.post('/requests')
def create_privacy_request(payload: PrivacyRequestCreate) -> dict:
    privacy_request_service.validate_request_type(payload.request_type)
    return {
        'status': 'created',
        'request_type': payload.request_type,
    }
