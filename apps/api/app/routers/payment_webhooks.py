from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.app.config import Settings, get_settings
from apps.api.app.database import get_db
from apps.api.app.schemas import PaymentWebhookResponse
from apps.api.app.services.audit_service import record_audit_event
from apps.api.app.services.payment_event_service import process_payment_webhook

router = APIRouter(prefix="/payment-webhooks", tags=["Payment webhooks"])


@router.post("/{provider}", response_model=PaymentWebhookResponse)
async def receive_payment_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PaymentWebhookResponse:
    raw_body = await request.body()
    signature = request.headers.get(settings.payment_webhook_signature_header)

    try:
        event, subscription, created = process_payment_webhook(
            db=db,
            settings=settings,
            provider=provider,
            raw_body=raw_body,
            signature=signature,
        )
    except PermissionError as exc:
        record_audit_event(
            db=db,
            request=request,
            action="payment.webhook_rejected",
            entity_type="PaymentEvent",
            meta={"provider": provider, "reason": str(exc)},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment webhook payload must be valid JSON",
        ) from exc
    except ValueError as exc:
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if "disabled" in str(exc).lower()
            else status.HTTP_400_BAD_REQUEST
        )
        record_audit_event(
            db=db,
            request=request,
            action="payment.webhook_failed",
            entity_type="PaymentEvent",
            meta={"provider": provider, "reason": str(exc)},
        )
        db.commit()
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    record_audit_event(
        db=db,
        request=request,
        action="payment.webhook_processed" if event.status == "processed" else "payment.webhook_ignored",
        entity_type="PaymentEvent",
        entity_id=str(event.id),
        meta={
            "provider": event.provider,
            "provider_event_id": event.provider_event_id,
            "event_type": event.event_type,
            "status": event.status,
            "created": created,
            "subscription_id": str(subscription.id) if subscription is not None else None,
        },
    )
    db.commit()

    return PaymentWebhookResponse(
        ok=True,
        status=event.status,
        provider=event.provider,
        event_id=event.provider_event_id,
        detail="Payment webhook accepted",
        subscription_id=str(subscription.id) if subscription is not None else None,
    )
