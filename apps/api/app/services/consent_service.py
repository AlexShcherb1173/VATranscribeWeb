from __future__ import annotations

import hashlib
from typing import Any

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.security_foundation.rate_limits import get_client_ip
from apps.api.app.models import LegalDocument, User, UserConsent
from apps.api.app.services.legal_document_service import (
    REQUIRED_LEGAL_DOCUMENT_TYPES,
    list_required_active_legal_documents,
    normalize_document_type,
)


def _hash_optional(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _get_client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    return get_client_ip(request)


def _get_user_agent(request: Request | None) -> str | None:
    if request is None:
        return None
    return request.headers.get("user-agent")


def _get_payload_value(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def normalize_acceptance_payload(items: list[Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}

    for item in items:
        document_type = normalize_document_type(str(_get_payload_value(item, "document_type") or ""))
        document_version = str(_get_payload_value(item, "document_version") or "")
        accepted = bool(_get_payload_value(item, "accepted"))

        if not document_type or not document_version:
            continue

        result[document_type] = {
            "document_type": document_type,
            "document_version": document_version,
            "accepted": accepted,
        }

    return result


def validate_required_consents(
    db: Session,
    accepted_legal_documents: list[Any],
) -> list[LegalDocument]:
    required_documents = list_required_active_legal_documents(db)
    accepted_map = normalize_acceptance_payload(accepted_legal_documents)

    missing: list[str] = []
    version_mismatch: list[str] = []

    for document in required_documents:
        item = accepted_map.get(document.document_type)

        if item is None or not item["accepted"]:
            missing.append(document.document_type)
            continue

        if item["document_version"] != document.version:
            version_mismatch.append(
                f"{document.document_type}: expected {document.version}, got {item['document_version']}"
            )

    if missing or version_mismatch:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Required legal documents must be accepted",
                "missing": missing,
                "version_mismatch": version_mismatch,
                "required_document_types": list(REQUIRED_LEGAL_DOCUMENT_TYPES),
            },
        )

    return required_documents


def record_user_consents(
    db: Session,
    user: User,
    request: Request | None,
    documents: list[LegalDocument],
) -> list[UserConsent]:
    ip_hash = _hash_optional(_get_client_ip(request))
    user_agent_hash = _hash_optional(_get_user_agent(request))

    rows: list[UserConsent] = []

    for document in documents:
        row = UserConsent(
            user_id=user.id,
            document_type=document.document_type,
            document_version=document.version,
            accepted=True,
            ip_hash=ip_hash,
            user_agent_hash=user_agent_hash,
        )
        db.add(row)
        rows.append(row)

    db.flush()

    return rows


def accept_current_required_consents(
    db: Session,
    user: User,
    request: Request | None,
) -> list[UserConsent]:
    documents = list_required_active_legal_documents(db)
    return record_user_consents(db=db, user=user, request=request, documents=documents)


def list_user_consents(
    db: Session,
    user: User,
) -> list[UserConsent]:
    return list(
        db.scalars(
            select(UserConsent)
            .where(UserConsent.user_id == user.id)
            .order_by(UserConsent.created_at.desc())
        )
    )


class ConsentService:
    def build_consent_record(
        self,
        user_id: int | str,
        document_type: str,
        document_version: str,
        accepted: bool = True,
    ) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "document_type": document_type,
            "document_version": document_version,
            "accepted": accepted,
        }


consent_service = ConsentService()
