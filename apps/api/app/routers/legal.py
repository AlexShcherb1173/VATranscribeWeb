from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.database import get_db
from apps.api.app.schemas import LegalDocumentRead
from apps.api.app.services.legal_document_service import (
    get_current_legal_document,
    list_active_legal_documents,
    list_required_active_legal_documents,
)

router = APIRouter(prefix="/legal", tags=["legal"])


@router.get("/documents", response_model=list[LegalDocumentRead])
def list_legal_documents(db: Session = Depends(get_db)) -> list:
    documents = list_active_legal_documents(db)
    db.commit()
    return documents


@router.get("/documents/current", response_model=list[LegalDocumentRead])
def list_current_required_legal_documents(db: Session = Depends(get_db)) -> list:
    documents = list_required_active_legal_documents(db)
    db.commit()
    return documents


@router.get("/documents/{document_type}/current", response_model=LegalDocumentRead)
def read_current_legal_document(
    document_type: str,
    db: Session = Depends(get_db),
):
    document = get_current_legal_document(db, document_type)
    db.commit()
    return document
