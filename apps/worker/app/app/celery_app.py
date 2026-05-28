from __future__ import annotations

from apps.worker.app.worker import celery

celery_app = celery

__all__ = ["celery", "celery_app"]
