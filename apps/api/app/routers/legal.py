from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix='/legal', tags=['legal'])


@router.get('/documents')
def list_legal_documents() -> dict[str, list[dict]]:
    return {'items': []}


@router.get('/documents/{document_type}/current')
def get_current_legal_document(document_type: str) -> dict:
    return {
        'document_type': document_type,
        'status': 'not_configured',
    }
