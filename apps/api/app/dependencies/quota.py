from fastapi import Depends
from sqlalchemy.orm import Session

from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import User
from apps.api.app.services.quota_service import assert_can_create_job


def require_job_quota(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    assert_can_create_job(db, current_user, jobs_to_add=1)
    return current_user