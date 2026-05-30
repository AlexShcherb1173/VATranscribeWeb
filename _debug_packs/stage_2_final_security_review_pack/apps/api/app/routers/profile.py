from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import User
from apps.api.app.schemas import UserProfileResponse, UserProfileUpdateRequest
from apps.api.app.services.account_bootstrap import ensure_user_profile

router = APIRouter(prefix="/profile")


@router.get(
    "",
    response_model=UserProfileResponse,
    summary="Get current user profile",
)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    profile = ensure_user_profile(db, current_user)
    return profile


@router.patch(
    "",
    response_model=UserProfileResponse,
    summary="Update current user profile",
)
def update_my_profile(
    payload: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    profile = ensure_user_profile(db, current_user)

    update_data = payload.model_dump(exclude_unset=True)

    for field_name, value in update_data.items():
        setattr(profile, field_name, value)

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile