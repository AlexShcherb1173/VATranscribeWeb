from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.app.config import Settings
from apps.api.app.models import PaymentEvent, Subscription
from apps.api.app.services.billing_service import activate_paid_subscription_from_verified_payment

ACTIVATION_EVENT_TYPES = {
    "payment.succeeded",
    "payment_succeeded",
    "subscription.activated",
    "subscription_activated",
    "checkout.session.completed",
}


def compute_webhook_signature(secret: str, raw_body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()


def verify_webhook_signature(secret: str, raw_body: bytes, signature: str | None) -> bool:
    if not secret or not signature:
        return False

    expected = compute_webhook_signature(secret, raw_body)
    candidate = signature.strip()
    if candidate.startswith("sha256="):
        candidate = candidate.removeprefix("sha256=")

    return hmac.compare_digest(expected, candidate)


def parse_webhook_payload(raw_body: bytes) -> dict[str, Any]:
    if not raw_body:
        return {}
    payload = json.loads(raw_body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Payment webhook payload must be a JSON object")
    return payload


def _metadata(payload: dict[str, Any]) -> dict[str, Any]:
    metadata = payload.get("metadata") or {}
    return metadata if isinstance(metadata, dict) else {}


def _payload_value(payload: dict[str, Any], *names: str) -> str | None:
    metadata = _metadata(payload)
    for name in names:
        value = payload.get(name)
        if value is None:
            value = metadata.get(name)
        if value is not None:
            return str(value)
    return None


def _event_type(payload: dict[str, Any]) -> str:
    return str(
        payload.get("event_type")
        or payload.get("type")
        or payload.get("event")
        or "unknown"
    ).strip().lower()


def _event_id(payload: dict[str, Any]) -> str:
    value = _payload_value(payload, "event_id", "id", "payment_id", "transaction_id")
    return value or str(uuid.uuid4())


def get_payment_event_by_key(db: Session, provider_event_key: str) -> PaymentEvent | None:
    return db.scalar(
        select(PaymentEvent).where(PaymentEvent.provider_event_key == provider_event_key)
    )


def record_payment_event_once(
    db: Session,
    *,
    provider: str,
    provider_event_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> tuple[PaymentEvent, bool]:
    provider_event_key = f"{provider}:{provider_event_id}"
    existing = get_payment_event_by_key(db, provider_event_key)
    if existing is not None:
        return existing, False

    event = PaymentEvent(
        id=str(uuid.uuid4()),
        provider=provider,
        provider_event_id=provider_event_id,
        provider_event_key=provider_event_key,
        event_type=event_type,
        status="received",
        payload=payload,
    )
    db.add(event)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = get_payment_event_by_key(db, provider_event_key)
        if existing is None:
            raise
        return existing, False
    return event, True


def process_payment_webhook(
    db: Session,
    *,
    settings: Settings,
    provider: str,
    raw_body: bytes,
    signature: str | None,
) -> tuple[PaymentEvent, Subscription | None, bool]:
    provider = provider.strip().lower()
    if settings.payment_provider == "disabled":
        raise ValueError("Payment provider is disabled")

    if provider != settings.payment_provider:
        raise ValueError("Payment webhook provider does not match configured PAYMENT_PROVIDER")

    if settings.is_production or settings.payment_webhook_secret:
        if not settings.payment_webhook_secret:
            raise PermissionError("PAYMENT_WEBHOOK_SECRET is required")
        if not verify_webhook_signature(settings.payment_webhook_secret, raw_body, signature):
            raise PermissionError("Invalid payment webhook signature")

    payload = parse_webhook_payload(raw_body)
    event_type = _event_type(payload)
    provider_event_id = _event_id(payload)
    event, created = record_payment_event_once(
        db=db,
        provider=provider,
        provider_event_id=provider_event_id,
        event_type=event_type,
        payload=payload,
    )

    if not created and event.status == "processed":
        return event, None, False

    subscription: Subscription | None = None

    try:
        if event_type in ACTIVATION_EVENT_TYPES:
            user_id = _payload_value(payload, "user_id", "customer_user_id")
            plan_code = _payload_value(payload, "plan_code", "plan")
            billing_period = _payload_value(payload, "billing_period", "period") or "monthly"
            if not user_id or not plan_code:
                raise ValueError("Payment activation event must include user_id and plan_code")

            _, subscription, _ = activate_paid_subscription_from_verified_payment(
                db=db,
                user_id=user_id,
                plan_code=plan_code,
                billing_period=billing_period,
            )
            event.status = "processed"
            event.processed_at = datetime.now(timezone.utc)
        else:
            event.status = "ignored"
            event.processed_at = datetime.now(timezone.utc)
    except Exception as exc:
        event.status = "failed"
        event.error_message = str(exc)
        db.add(event)
        db.commit()
        raise

    db.add(event)
    db.commit()
    db.refresh(event)
    return event, subscription, created
