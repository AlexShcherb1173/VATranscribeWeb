from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from apps.api.app.config import Settings


class JsonLogFormatter(logging.Formatter):
    """Container-friendly JSON formatter with request/correlation support."""

    _reserved = {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "asctime",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in self._reserved:
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except TypeError:
                payload[key] = str(value)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(settings: Settings) -> None:
    """Configure stdout logs for Docker/Loki/collector ingestion."""
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


def init_sentry(settings: Settings, *, service: str = "api") -> None:
    """Initialize Sentry/APM when SENTRY_DSN is configured.

    service="api" enables FastAPI/SQLAlchemy integrations.
    service="worker" enables Celery integration.
    """
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    except Exception as exc:  # pragma: no cover
        logging.getLogger(__name__).warning("Sentry initialization skipped: %s", exc)
        return

    integrations: list[Any] = [
        SqlalchemyIntegration(),
        LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
    ]

    if service == "api":
        try:
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            integrations.append(FastApiIntegration())
        except Exception as exc:  # pragma: no cover
            logging.getLogger(__name__).warning("FastAPI Sentry integration skipped: %s", exc)

    if service == "worker" and settings.sentry_worker_enabled:
        try:
            from sentry_sdk.integrations.celery import CeleryIntegration
            integrations.append(CeleryIntegration())
        except Exception as exc:  # pragma: no cover
            logging.getLogger(__name__).warning("Celery Sentry integration skipped: %s", exc)

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment or settings.app_env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        integrations=integrations,
        send_default_pii=False,
        release=settings.release_version,
        server_name=service,
    )
