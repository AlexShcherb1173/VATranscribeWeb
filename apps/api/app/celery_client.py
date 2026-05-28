from celery import Celery

from apps.api.app.config import get_settings

settings = get_settings()

celery_client = Celery(
    "vatranscribe_api_client",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
