from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import User
from apps.api.app.schemas import (
    PrivacyOverviewResponse,
    PrivacyRequestCreate,
    PrivacyRequestRead,
)
from apps.api.app.services.audit_service import record_audit_event
from apps.api.app.services.privacy_request_service import (
    create_user_privacy_request,
    list_user_privacy_requests,
)


router = APIRouter(prefix='/privacy', tags=['privacy'])


@router.get('/me', response_model=PrivacyOverviewResponse)
def get_my_privacy_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PrivacyOverviewResponse:
    rows = list_user_privacy_requests(db, current_user)
    return PrivacyOverviewResponse(status='ok', requests=rows)


@router.post(
    '/requests',
    response_model=PrivacyRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def create_privacy_request(
    payload: PrivacyRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PrivacyRequestRead:
    row = create_user_privacy_request(
        db=db,
        user=current_user,
        request_type=payload.request_type,
        comment=payload.comment,
    )

    record_audit_event(
        db=db,
        request=request,
        action='privacy.request_created',
        actor_user_id=str(current_user.id),
        entity_type='PrivacyRequest',
        entity_id=str(row.id),
        meta={
            'request_type': row.request_type,
            'status': row.status,
        },
    )

    db.commit()
    db.refresh(row)

    return row
