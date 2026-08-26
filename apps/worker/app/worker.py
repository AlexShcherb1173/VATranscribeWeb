from __future__ import annotations

from celery import Celery, signals

from apps.api.app.config import get_settings
from apps.api.app.observability import configure_logging, init_sentry

settings = get_settings()
configure_logging(settings)
init_sentry(settings, service="worker")


@signals.setup_logging.connect
def configure_celery_logging(**_: object) -> None:
    """Keep Celery worker logs on the application JSON formatter."""
    configure_logging(settings)


celery = Celery(
    "vatranscribe_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["apps.worker.app.tasks.jobs"],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60 * 60 * 6,
    task_soft_time_limit=60 * 60 * 5,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
)

celery.autodiscover_tasks(["apps.worker.app.tasks"], force=True)
