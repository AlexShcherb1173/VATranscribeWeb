from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import User
from apps.api.app.schemas import ConsentAcceptCurrentResponse, UserConsentRead
from apps.api.app.services.audit_service import record_audit_event
from apps.api.app.services.consent_service import (
    accept_current_required_consents,
    list_user_consents,
)

router = APIRouter(prefix="/consents", tags=["consents"])


@router.get("/me", response_model=list[UserConsentRead])
def list_my_consents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    return list_user_consents(db, current_user)


@router.post("/accept-current", response_model=ConsentAcceptCurrentResponse)
def accept_current_consents(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsentAcceptCurrentResponse:
    rows = accept_current_required_consents(
        db=db,
        user=current_user,
        request=request,
    )

    record_audit_event(
        db=db,
        request=request,
        action="legal.consents_accepted",
        actor_user_id=str(current_user.id),
        entity_type="User",
        entity_id=str(current_user.id),
        meta={
            "documents": [
                {
                    "document_type": row.document_type,
                    "document_version": row.document_version,
                }
                for row in rows
            ],
        },
    )

    db.commit()

    return ConsentAcceptCurrentResponse(items=rows)
