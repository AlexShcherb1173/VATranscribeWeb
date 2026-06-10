from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from apps.api.app.config import Settings

logger = logging.getLogger(__name__)

SAFE_STATUS_MESSAGES = {
    400: "Bad request",
    401: "Authentication required",
    403: "Access denied",
    404: "Resource not found",
    409: "Request conflict",
    422: "Validation failed",
    429: "Too many requests",
    500: "Internal server error",
    502: "Bad gateway",
    503: "Service unavailable",
}


def _request_id(request: Request, settings: Settings) -> str | None:
    header_name = getattr(settings, "request_id_header", "X-Request-ID")
    return request.headers.get(header_name) or getattr(request.state, "request_id", None)


def _safe_detail(status_code: int, detail: Any, settings: Settings) -> str:
    if status_code == 404:
        return SAFE_STATUS_MESSAGES[404]

    if status_code < 500 and not settings.is_production:
        return str(detail) if detail else SAFE_STATUS_MESSAGES.get(status_code, "Request failed")

    return SAFE_STATUS_MESSAGES.get(status_code, "Request failed")


def _payload(status_code: int, message: str, request_id: str | None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "error": True,
        "status_code": status_code,
        "message": message,
    }
    if request_id:
        body["request_id"] = request_id
    return body


def register_exception_handlers(app: FastAPI, *, settings: Settings) -> None:
    """Register production-safe API error handlers.

    Production responses must not expose stack traces, exception class names,
    SQL errors, filesystem paths or framework internals.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = _request_id(request, settings)
        message = _safe_detail(exc.status_code, exc.detail, settings)
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(exc.status_code, message, request_id),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = _request_id(request, settings)
        if settings.is_production:
            message = SAFE_STATUS_MESSAGES[422]
        else:
            message = str(exc)
        return JSONResponse(
            status_code=422,
            content=_payload(422, message, request_id),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = _request_id(request, settings)
        logger.exception(
            "Unhandled API error",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=500,
            content=_payload(500, SAFE_STATUS_MESSAGES[500], request_id),
        )
