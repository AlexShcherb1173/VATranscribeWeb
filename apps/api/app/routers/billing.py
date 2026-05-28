from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import User
from apps.api.app.schemas import (
    BillingOverviewResponse,
    BillingUpgradeRequest,
    BillingUpgradeResponse,
)
from apps.api.app.services.billing_service import get_billing_overview, upgrade_user_plan

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/overview", response_model=BillingOverviewResponse)
def billing_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BillingOverviewResponse:
    return BillingOverviewResponse(**get_billing_overview(db, current_user))


@router.post("/upgrade", response_model=BillingUpgradeResponse)
def billing_upgrade(
    payload: BillingUpgradeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BillingUpgradeResponse:
    try:
        current_plan, subscription, quota = upgrade_user_plan(
            db=db,
            user=current_user,
            plan_code=payload.plan_code,
            billing_period=payload.billing_period,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return BillingUpgradeResponse(
        current_plan=current_plan,
        subscription=subscription,
        quota=quota,
    )
