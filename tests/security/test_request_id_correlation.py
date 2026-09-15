from __future__ import annotations

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.exception_handlers import register_exception_handlers
from apps.api.app.main import request_id_and_access_log_middleware, settings


CUSTOM_REQUEST_ID = "p3-correlation-client-id-001"


def _build_client() -> TestClient:
    test_app = FastAPI(debug=False)

    register_exception_handlers(
        test_app,
        settings=settings,
    )

    test_app.middleware("http")(
        request_id_and_access_log_middleware
    )

    @test_app.get("/ok")
    def ok() -> dict[str, bool]:
        return {"ok": True}

    @test_app.get("/validate")
    def validate(value: int) -> dict[str, int]:
        return {"value": value}

    @test_app.get("/fail")
    def fail() -> None:
        raise RuntimeError(
            "request-id correlation test failure"
        )

    return TestClient(
        test_app,
        raise_server_exceptions=False,
    )


def _generated_request_id(value: str | None) -> str:
    assert value is not None
    assert len(value) == 32
    int(value, 16)
    return value


def test_success_generated_request_id_matches_structured_log() -> None:
    client = _build_client()

    with patch(
        "apps.api.app.main.request_logger.info"
    ) as completed_log:
        response = client.get("/ok")

    assert response.status_code == 200

    request_id = _generated_request_id(
        response.headers.get(
            settings.request_id_header
        )
    )

    assert completed_log.call_count == 1
    assert (
        completed_log.call_args.kwargs["extra"]["request_id"]
        == request_id
    )


def test_success_client_request_id_is_preserved() -> None:
    client = _build_client()

    response = client.get(
        "/ok",
        headers={
            settings.request_id_header:
                CUSTOM_REQUEST_ID,
        },
    )

    assert response.status_code == 200
    assert (
        response.headers.get(
            settings.request_id_header
        )
        == CUSTOM_REQUEST_ID
    )


def test_404_generated_request_id_matches_body_and_header() -> None:
    client = _build_client()

    response = client.get("/missing")

    assert response.status_code == 404

    request_id = _generated_request_id(
        response.headers.get(
            settings.request_id_header
        )
    )

    assert response.json()["request_id"] == request_id


def test_422_generated_request_id_matches_body_and_header() -> None:
    client = _build_client()

    response = client.get(
        "/validate",
        params={
            "value": "not-an-int",
        },
    )

    assert response.status_code == 422

    request_id = _generated_request_id(
        response.headers.get(
            settings.request_id_header
        )
    )

    assert response.json()["request_id"] == request_id


def test_500_generated_request_id_matches_body_header_and_logs() -> None:
    client = _build_client()

    with (
        patch(
            "apps.api.app.main.request_logger.exception"
        ) as request_log,
        patch(
            "apps.api.app.exception_handlers.logger.exception"
        ) as handler_log,
    ):
        response = client.get("/fail")

    assert response.status_code == 500
    assert response.headers[
        "content-type"
    ].startswith("application/json")

    request_id = _generated_request_id(
        response.headers.get(
            settings.request_id_header
        )
    )

    assert response.json()["request_id"] == request_id

    assert request_log.call_count == 1
    assert handler_log.call_count == 1

    assert (
        request_log.call_args.kwargs["extra"]["request_id"]
        == request_id
    )

    assert (
        handler_log.call_args.kwargs["extra"]["request_id"]
        == request_id
    )


def test_500_client_request_id_matches_body_header_and_logs() -> None:
    client = _build_client()

    with (
        patch(
            "apps.api.app.main.request_logger.exception"
        ) as request_log,
        patch(
            "apps.api.app.exception_handlers.logger.exception"
        ) as handler_log,
    ):
        response = client.get(
            "/fail",
            headers={
                settings.request_id_header:
                    CUSTOM_REQUEST_ID,
            },
        )

    assert response.status_code == 500

    assert (
        response.headers.get(
            settings.request_id_header
        )
        == CUSTOM_REQUEST_ID
    )

    assert (
        response.json()["request_id"]
        == CUSTOM_REQUEST_ID
    )

    assert (
        request_log.call_args.kwargs["extra"]["request_id"]
        == CUSTOM_REQUEST_ID
    )

    assert (
        handler_log.call_args.kwargs["extra"]["request_id"]
        == CUSTOM_REQUEST_ID
    )
