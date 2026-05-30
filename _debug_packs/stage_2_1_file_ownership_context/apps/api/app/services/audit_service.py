from __future__ import annotations

from typing import Any


class AuditService:
    def build_event(
        self,
        action: str,
        actor_user_id: int | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            'action': action,
            'actor_user_id': actor_user_id,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'meta': meta or {},
        }


audit_service = AuditService()
