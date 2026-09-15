from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.app.config import Settings, get_settings
from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import User
from apps.api.app.schemas import (
    BillingOverviewResponse,
    BillingUpgradeRequest,
    BillingUpgradeResponse,
)
from apps.api.app.services.audit_service import record_audit_event
from apps.api.app.services.billing_service import (
    BillingUpgradeForbidden,
    get_billing_overview,
    upgrade_user_plan,
)

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/overview", response_model=BillingOverviewResponse)
def billing_overview(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BillingOverviewResponse:
    result = get_billing_overview(db, current_user)

    record_audit_event(
        db=db,
        request=request,
        action="billing.overview_viewed",
        actor_user_id=str(current_user.id),
        entity_type="User",
        entity_id=str(current_user.id),
    )
    db.commit()

    return BillingOverviewResponse(**result)


@router.post("/upgrade", response_model=BillingUpgradeResponse)
def billing_upgrade(
    payload: BillingUpgradeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> BillingUpgradeResponse:
    record_audit_event(
        db=db,
        request=request,
        action="billing.upgrade_requested",
        actor_user_id=str(current_user.id),
        entity_type="User",
        entity_id=str(current_user.id),
        meta={
            "plan_code": payload.plan_code,
            "billing_period": payload.billing_period,
        },
    )

    try:
        current_plan, subscription, quota = upgrade_user_plan(
            db=db,
            user=current_user,
            plan_code=payload.plan_code,
            billing_period=payload.billing_period,
            allow_fake_upgrade=settings.fake_billing_upgrade_allowed,
        )
    except BillingUpgradeForbidden as exc:
        record_audit_event(
            db=db,
            request=request,
            action="billing.upgrade_blocked",
            actor_user_id=str(current_user.id),
            entity_type="User",
            entity_id=str(current_user.id),
            meta={
                "plan_code": payload.plan_code,
                "billing_period": payload.billing_period,
                "payment_provider": settings.payment_provider,
                "billing_fake_upgrade_enabled": settings.billing_fake_upgrade_enabled,
                "reason": str(exc),
            },
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        record_audit_event(
            db=db,
            request=request,
            action="billing.upgrade_failed",
            actor_user_id=str(current_user.id),
            entity_type="User",
            entity_id=str(current_user.id),
            meta={
                "plan_code": payload.plan_code,
                "billing_period": payload.billing_period,
                "reason": str(exc),
            },
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    record_audit_event(
        db=db,
        request=request,
        action="billing.upgrade_succeeded",
        actor_user_id=str(current_user.id),
        entity_type="Subscription",
        entity_id=str(subscription.id),
        meta={
            "plan_code": payload.plan_code,
            "billing_period": payload.billing_period,
            "subscription_id": str(subscription.id),
            "plan_id": str(current_plan.id),
        },
    )
    db.commit()

    return BillingUpgradeResponse(
        current_plan=current_plan,
        subscription=subscription,
        quota=quota,
    )
