from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import User
from apps.api.app.schemas import UserQuotaResponse
from apps.api.app.services.quota_service import get_or_create_quota

router = APIRouter(prefix="/quota")


@router.get(
    "/me",
    response_model=UserQuotaResponse,
    summary="Get current user quota",
)
def get_my_quota(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserQuotaResponse:
    quota = get_or_create_quota(db, current_user)
    return quota