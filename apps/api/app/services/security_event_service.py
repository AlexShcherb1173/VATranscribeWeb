from __future__ import annotations


class SecurityEventService:
    def normalize_severity(self, severity: str) -> str:
        normalized = severity.strip().lower()
        if normalized not in {'low', 'medium', 'high', 'critical'}:
            return 'medium'
        return normalized


security_event_service = SecurityEventService()
