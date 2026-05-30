from __future__ import annotations

from typing import Any


class ConsentService:
    def build_consent_record(
        self,
        user_id: int,
        document_type: str,
        document_version: str,
        accepted: bool = True,
    ) -> dict[str, Any]:
        return {
            'user_id': user_id,
            'document_type': document_type,
            'document_version': document_version,
            'accepted': accepted,
        }


consent_service = ConsentService()
