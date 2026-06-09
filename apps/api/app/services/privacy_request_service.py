from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.models import PrivacyRequest, User


ALLOWED_PRIVACY_REQUEST_TYPES: set[str] = {
    'export',
    'delete_account',
    'delete_files',
    'revoke_consent',
}


def ensure_valid_privacy_request_type(request_type: str) -> None:
    if request_type not in ALLOWED_PRIVACY_REQUEST_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Unsupported privacy request type',
        )


def create_user_privacy_request(
    db: Session,
    user: User,
    request_type: str,
    comment: str | None = None,
) -> PrivacyRequest:
    ensure_valid_privacy_request_type(request_type)

    row = PrivacyRequest(
        user_id=user.id,
        request_type=request_type,
        status='pending',
        comment=comment,
    )

    db.add(row)
    db.flush()

    return row


def list_user_privacy_requests(
    db: Session,
    user: User,
) -> list[PrivacyRequest]:
    return list(
        db.scalars(
            select(PrivacyRequest)
            .where(PrivacyRequest.user_id == user.id)
            .order_by(PrivacyRequest.created_at.desc())
        )
    )


class PrivacyRequestService:
    allowed_request_types = ALLOWED_PRIVACY_REQUEST_TYPES

    def validate_request_type(self, request_type: str) -> None:
        if request_type not in self.allowed_request_types:
            raise ValueError('Unsupported privacy request type')


privacy_request_service = PrivacyRequestService()
