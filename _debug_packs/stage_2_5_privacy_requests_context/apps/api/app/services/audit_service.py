from __future__ import annotations

import hashlib
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from apps.api.app.models import AuditLog


def _hash_optional(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _get_client_ip(request: Request | None) -> str | None:
    if request is None:
        return None

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    if request.client:
        return request.client.host

    return None


def _get_user_agent(request: Request | None) -> str | None:
    if request is None:
        return None
    return request.headers.get("user-agent")


def record_audit_event(
    db: Session,
    action: str,
    request: Request | None = None,
    actor_user_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> AuditLog:
    event = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        meta_json=meta or {},
        ip_hash=_hash_optional(_get_client_ip(request)),
        user_agent_hash=_hash_optional(_get_user_agent(request)),
    )
    db.add(event)
    db.flush()
    return event
