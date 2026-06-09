from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.database import get_db
from apps.api.app.schemas import BillingPlanResponse
from apps.api.app.services.billing_service import get_available_plans, get_plan_by_code

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.get("", response_model=list[BillingPlanResponse])
def list_public_plans(
    db: Session = Depends(get_db),
) -> list[BillingPlanResponse]:
    """
    Public plan catalog endpoint.

    Used by marketing/web pricing pages as the backend source of truth for:
    - plan codes
    - monthly prices
    - quotas
    - active plan availability

    This endpoint does not require authentication.
    """
    return get_available_plans(db)


@router.get("/{plan_code}", response_model=BillingPlanResponse)
def get_public_plan(
    plan_code: str,
    db: Session = Depends(get_db),
) -> BillingPlanResponse:
    """
    Public active plan lookup by code.
    """
    try:
        return get_plan_by_code(db, plan_code)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc