from __future__ import annotations


class LegalDocumentService:
    def normalize_document_type(self, document_type: str) -> str:
        return document_type.strip().lower().replace(' ', '_')


legal_document_service = LegalDocumentService()
