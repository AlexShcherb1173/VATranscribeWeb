from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.models import LegalDocument

REQUIRED_LEGAL_DOCUMENT_TYPES: tuple[str, ...] = (
    "terms",
    "privacy",
    "personal_data",
)

DEFAULT_LEGAL_DOCUMENTS: tuple[dict[str, str], ...] = (
    {
        "document_type": "terms",
        "version": "1.0",
        "title": "Terms of Service",
        "content": "Default Terms of Service placeholder. Replace with final legal text before production.",
    },
    {
        "document_type": "privacy",
        "version": "1.0",
        "title": "Privacy Policy",
        "content": "Default Privacy Policy placeholder. Replace with final legal text before production.",
    },
    {
        "document_type": "personal_data",
        "version": "1.0",
        "title": "Personal Data Processing Consent",
        "content": "Default personal data processing consent placeholder. Replace with final legal text before production.",
    },
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_document_type(document_type: str) -> str:
    return document_type.strip().lower().replace(" ", "_").replace("-", "_")


def ensure_default_legal_documents(db: Session) -> None:
    for item in DEFAULT_LEGAL_DOCUMENTS:
        document_type = normalize_document_type(item["document_type"])

        existing = db.scalar(
            select(LegalDocument).where(
                LegalDocument.document_type == document_type,
                LegalDocument.version == item["version"],
            )
        )

        if existing is not None:
            if not existing.is_active:
                existing.is_active = True
            if existing.published_at is None:
                existing.published_at = utcnow()
            continue

        db.add(
            LegalDocument(
                document_type=document_type,
                version=item["version"],
                title=item["title"],
                content=item["content"],
                is_active=True,
                published_at=utcnow(),
            )
        )

    db.flush()


def list_active_legal_documents(db: Session) -> list[LegalDocument]:
    ensure_default_legal_documents(db)

    return list(
        db.scalars(
            select(LegalDocument)
            .where(LegalDocument.is_active.is_(True))
            .order_by(LegalDocument.document_type.asc(), LegalDocument.published_at.desc())
        )
    )


def get_current_legal_document(db: Session, document_type: str) -> LegalDocument:
    ensure_default_legal_documents(db)

    normalized = normalize_document_type(document_type)

    document = db.scalar(
        select(LegalDocument)
        .where(
            LegalDocument.document_type == normalized,
            LegalDocument.is_active.is_(True),
        )
        .order_by(LegalDocument.published_at.desc(), LegalDocument.created_at.desc())
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active legal document '{normalized}' not found",
        )

    return document


def list_required_active_legal_documents(db: Session) -> list[LegalDocument]:
    ensure_default_legal_documents(db)

    return [
        get_current_legal_document(db, document_type)
        for document_type in REQUIRED_LEGAL_DOCUMENT_TYPES
    ]


class LegalDocumentService:
    def normalize_document_type(self, document_type: str) -> str:
        return normalize_document_type(document_type)


legal_document_service = LegalDocumentService()
