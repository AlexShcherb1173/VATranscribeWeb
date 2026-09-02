from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

from apps.api.app.config import Settings


_SENTRY_REDACTED = "[Filtered]"

_SENTRY_SENSITIVE_FIELDS = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "api-key",
        "password",
        "passwd",
        "secret",
        "client-secret",
        "access-token",
        "refresh-token",
        "id-token",
        "csrf-token",
        "x-csrf-token",
        "sentry-dsn",
    }
)


def _normalize_sentry_field_name(value: Any) -> str:
    if isinstance(value, (bytes, bytearray)):
        text = bytes(value).decode(
            "latin-1",
            errors="replace",
        )
    else:
        text = str(value)

    return (
        text
        .strip()
        .lower()
        .replace("_", "-")
    )


def _sentry_header_value(
    headers: Any,
    header_name: str,
) -> str | None:
    expected = header_name.strip().lower()

    if isinstance(headers, dict):
        for key, value in headers.items():
            if str(key).strip().lower() == expected:
                return str(value)

        return None

    if isinstance(headers, (list, tuple)):
        for item in headers:
            if (
                isinstance(item, (list, tuple))
                and len(item) == 2
                and str(item[0]).strip().lower()
                == expected
            ):
                return str(item[1])

    return None


def _redact_sentry_headers(headers: Any) -> Any:
    if isinstance(headers, dict):
        return {
            key: (
                _SENTRY_REDACTED
                if _normalize_sentry_field_name(key)
                in _SENTRY_SENSITIVE_FIELDS
                else value
            )
            for key, value in headers.items()
        }

    if isinstance(headers, (list, tuple)):
        redacted: list[Any] = []

        for item in headers:
            if (
                isinstance(item, (list, tuple))
                and len(item) == 2
            ):
                key, value = item

                if (
                    _normalize_sentry_field_name(key)
                    in _SENTRY_SENSITIVE_FIELDS
                ):
                    value = _SENTRY_REDACTED

                redacted.append(
                    [key, value]
                )
            else:
                redacted.append(item)

        return redacted

    return headers


def _redact_sentry_value(
    value: Any,
    *,
    field_name: Any | None = None,
) -> Any:
    normalized_field_name = (
        _normalize_sentry_field_name(
            field_name
        )
        if field_name is not None
        else None
    )

    if (
        normalized_field_name
        in _SENTRY_SENSITIVE_FIELDS
    ):
        return _SENTRY_REDACTED

    # ASGI request/scope/connection objects can be
    # captured inside Sentry stack-frame local vars.
    # Their headers are usually represented as
    # key/value pair lists rather than dictionaries.
    if normalized_field_name == "headers":
        value = _redact_sentry_headers(
            value
        )

    if isinstance(value, dict):
        return {
            key: _redact_sentry_value(
                item,
                field_name=key,
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            _redact_sentry_value(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            _redact_sentry_value(item)
            for item in value
        ]

    return value


def _build_sentry_before_send(
    request_id_header: str,
):
    """Build a transport-boundary sanitizer.

    Sensitive request values must be removed before the
    event leaves the process. The callback also restores
    request metadata on framework-native exception events.
    """

    def before_send(
        event: dict[str, Any],
        hint: dict[str, Any],
    ) -> dict[str, Any] | None:
        del hint

        request = event.get("request")

        if isinstance(request, dict):
            headers = request.get("headers")

            request_id = _sentry_header_value(
                headers,
                request_id_header,
            )

            extra = event.get("extra")

            if not isinstance(extra, dict):
                extra = {}
                event["extra"] = extra

            if request_id:
                extra.setdefault(
                    "request_id",
                    request_id,
                )

            method = request.get("method")

            if method:
                extra.setdefault(
                    "method",
                    str(method),
                )

            url = request.get("url")

            if url:
                path = urlsplit(
                    str(url)
                ).path

                if path:
                    extra.setdefault(
                        "path",
                        path,
                    )

            request["headers"] = (
                _redact_sentry_headers(
                    headers
                )
            )

        redacted = _redact_sentry_value(
            event
        )

        if not isinstance(redacted, dict):
            return None

        return redacted

    return before_send


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
        LoggingIntegration(level=logging.INFO, event_level=None),
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
        # Do not send Python frame local variables.
        #
        # ASGI Request/scope/connection objects can
        # contain Authorization, Cookie and other
        # credentials. Sentry serializes frame locals
        # under exception.stacktrace.frames[*].vars.
        # Keep the stack trace itself, but exclude the
        # local-variable snapshot at the SDK boundary.
        include_local_variables=False,
        release=settings.release_version,
        server_name=service,
        before_send=_build_sentry_before_send(
            settings.request_id_header
        ),
    )
