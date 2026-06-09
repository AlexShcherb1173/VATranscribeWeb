from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from apps.api.app.config import Settings


class JsonLogFormatter(logging.Formatter):
    """Minimal JSON formatter for container-friendly structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(settings: Settings) -> None:
    """Configure application logs for Docker/stdout collection."""
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    root.addHandler(handler)
    root.setLevel(settings.log_level_upper)
    logging.getLogger("uvicorn.access").setLevel(settings.log_level_upper)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def init_sentry(settings: Settings) -> None:
    """Initialize Sentry/APM only when SENTRY_DSN is configured."""
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    except Exception as exc:  # pragma: no cover
        logging.getLogger(__name__).warning("Sentry initialization skipped: %s", exc)
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        send_default_pii=False,
        release=settings.release_version,
    )
