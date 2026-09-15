from __future__ import annotations

from apps.api.app.observability import (
    _SENTRY_REDACTED,
    _build_sentry_before_send,
)


def test_backend_sentry_before_send_redacts_sensitive_headers_and_enriches_metadata():
    before_send = _build_sentry_before_send(
        "X-Request-ID"
    )

    event = {
        "request": {
            "method": "GET",
            "url": (
                "http://testserver/"
                "api/v1/sentry-probe?safe=1"
            ),
            "headers": {
                "Authorization": (
                    "Bearer must-not-leave-process"
                ),
                "Cookie": (
                    "session=must-not-leave-process"
                ),
                "X-API-Key": (
                    "must-not-leave-process"
                ),
                "X-Request-ID": "request-123",
                "User-Agent": "pytest",
            },
        },
        "extra": {
            "safe": "keep-me",
            "password": "must-not-leave-process",
        },
    }

    result = before_send(
        event,
        {},
    )

    assert result is not None

    headers = result["request"]["headers"]

    assert (
        headers["Authorization"]
        == _SENTRY_REDACTED
    )
    assert (
        headers["Cookie"]
        == _SENTRY_REDACTED
    )
    assert (
        headers["X-API-Key"]
        == _SENTRY_REDACTED
    )

    assert (
        headers["X-Request-ID"]
        == "request-123"
    )
    assert (
        headers["User-Agent"]
        == "pytest"
    )

    assert (
        result["extra"]["password"]
        == _SENTRY_REDACTED
    )
    assert (
        result["extra"]["safe"]
        == "keep-me"
    )

    assert (
        result["extra"]["request_id"]
        == "request-123"
    )
    assert (
        result["extra"]["method"]
        == "GET"
    )
    assert (
        result["extra"]["path"]
        == "/api/v1/sentry-probe"
    )


def test_backend_sentry_before_send_handles_header_pair_lists():
    before_send = _build_sentry_before_send(
        "X-Request-ID"
    )

    event = {
        "request": {
            "method": "POST",
            "url": (
                "https://api.example.test/"
                "api/v1/jobs"
            ),
            "headers": [
                [
                    "authorization",
                    "Bearer secret-value",
                ],
                [
                    "cookie",
                    "session=secret-value",
                ],
                [
                    "x-request-id",
                    "request-456",
                ],
            ],
        },
    }

    result = before_send(
        event,
        {},
    )

    assert result is not None

    headers = result["request"]["headers"]

    assert headers[0] == [
        "authorization",
        _SENTRY_REDACTED,
    ]
    assert headers[1] == [
        "cookie",
        _SENTRY_REDACTED,
    ]
    assert headers[2] == [
        "x-request-id",
        "request-456",
    ]

    assert (
        result["extra"]["request_id"]
        == "request-456"
    )
    assert (
        result["extra"]["method"]
        == "POST"
    )
    assert (
        result["extra"]["path"]
        == "/api/v1/jobs"
    )



def test_backend_sentry_before_send_redacts_nested_stacktrace_header_containers():
    before_send = _build_sentry_before_send(
        "X-Request-ID"
    )

    auth_marker = (
        "nested-auth-secret-"
        "must-not-leave-process"
    )

    cookie_marker = (
        "nested-cookie-secret-"
        "must-not-leave-process"
    )

    event = {
        "exception": {
            "values": [
                {
                    "type": "RuntimeError",
                    "value": "controlled failure",
                    "stacktrace": {
                        "frames": [
                            {
                                "vars": {
                                    "request": {
                                        "headers": [
                                            [
                                                "authorization",
                                                (
                                                    "Bearer "
                                                    + auth_marker
                                                ),
                                            ],
                                            [
                                                "cookie",
                                                (
                                                    "session="
                                                    + cookie_marker
                                                ),
                                            ],
                                            [
                                                "x-request-id",
                                                "request-nested-1",
                                            ],
                                        ],
                                    },
                                    "scope": {
                                        # ASGI uses byte pairs.
                                        "headers": [
                                            [
                                                b"authorization",
                                                (
                                                    b"Bearer "
                                                    + auth_marker.encode(
                                                        "ascii"
                                                    )
                                                ),
                                            ],
                                            [
                                                b"cookie",
                                                (
                                                    b"session="
                                                    + cookie_marker.encode(
                                                        "ascii"
                                                    )
                                                ),
                                            ],
                                            [
                                                b"x-request-id",
                                                b"request-nested-1",
                                            ],
                                        ],
                                    },
                                    "conn": {
                                        "headers": {
                                            "Authorization": (
                                                "Bearer "
                                                + auth_marker
                                            ),
                                            "Cookie": (
                                                "session="
                                                + cookie_marker
                                            ),
                                            "X-Request-ID": (
                                                "request-nested-1"
                                            ),
                                        },
                                    },
                                    "ordinary_local": (
                                        "keep-this-diagnostic-value"
                                    ),
                                },
                            },
                        ],
                    },
                },
            ],
        },
    }

    result = before_send(
        event,
        {},
    )

    assert result is not None

    frame_vars = (
        result["exception"]
        ["values"][0]
        ["stacktrace"]
        ["frames"][0]
        ["vars"]
    )

    request_headers = (
        frame_vars["request"]["headers"]
    )

    assert request_headers[0][1] == (
        _SENTRY_REDACTED
    )

    assert request_headers[1][1] == (
        _SENTRY_REDACTED
    )

    assert request_headers[2][1] == (
        "request-nested-1"
    )

    scope_headers = (
        frame_vars["scope"]["headers"]
    )

    assert scope_headers[0][1] == (
        _SENTRY_REDACTED
    )

    assert scope_headers[1][1] == (
        _SENTRY_REDACTED
    )

    # Non-sensitive ASGI header remains available.
    assert scope_headers[2][1] == (
        b"request-nested-1"
    )

    conn_headers = (
        frame_vars["conn"]["headers"]
    )

    assert conn_headers["Authorization"] == (
        _SENTRY_REDACTED
    )

    assert conn_headers["Cookie"] == (
        _SENTRY_REDACTED
    )

    assert conn_headers["X-Request-ID"] == (
        "request-nested-1"
    )

    # Do not destroy unrelated forensic locals.
    assert frame_vars["ordinary_local"] == (
        "keep-this-diagnostic-value"
    )

    result_text = repr(result)

    assert auth_marker not in result_text
    assert cookie_marker not in result_text
