from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import subprocess
import sys

from apps.api.app.observability import JsonLogFormatter


ROOT = Path(__file__).resolve().parents[2]


def _record(
    *,
    logger_name: str,
    message: object,
    args: object = (),
    **extra: object,
) -> logging.LogRecord:
    record = logging.LogRecord(
        name=logger_name,
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=args,
        exc_info=None,
    )

    for key, value in extra.items():
        setattr(
            record,
            key,
            value,
        )

    return record


def test_json_formatter_redacts_sensitive_structured_extras() -> None:
    markers = {
        "authorization": "P3LOG_AUTH_RAW_01",
        "cookie": "P3LOG_COOKIE_RAW_02",
        "password": "P3LOG_PASSWORD_RAW_03",
        "api_key": "P3LOG_API_KEY_RAW_04",
    }

    record = _record(
        logger_name="app.security",
        message="structured log",
        authorization=markers["authorization"],
        cookie=markers["cookie"],
        password=markers["password"],
        api_key=markers["api_key"],
        nested={
            "authorization": markers["authorization"],
            "cookie": markers["cookie"],
            "password": markers["password"],
            "api_key": markers["api_key"],
        },
    )

    output = JsonLogFormatter().format(
        record
    )

    payload = json.loads(
        output
    )

    assert payload["authorization"] == "[Filtered]"
    assert payload["cookie"] == "[Filtered]"
    assert payload["password"] == "[Filtered]"
    assert payload["api_key"] == "[Filtered]"

    assert payload["nested"]["authorization"] == "[Filtered]"
    assert payload["nested"]["cookie"] == "[Filtered]"
    assert payload["nested"]["password"] == "[Filtered]"
    assert payload["nested"]["api_key"] == "[Filtered]"

    for marker in markers.values():
        assert marker not in output


def test_json_formatter_redacts_sensitive_mapping_message_args() -> None:
    markers = {
        "authorization": "P3LOG_MSG_AUTH_RAW_11",
        "cookie": "P3LOG_MSG_COOKIE_RAW_12",
        "password": "P3LOG_MSG_PASSWORD_RAW_13",
        "api_key": "P3LOG_MSG_API_KEY_RAW_14",
    }

    record = _record(
        logger_name="app.message",
        message="payload=%r",
        args=(
            {
                "authorization": markers["authorization"],
                "cookie": markers["cookie"],
                "password": markers["password"],
                "api_key": markers["api_key"],
            },
        ),
    )

    output = JsonLogFormatter().format(
        record
    )

    assert "[Filtered]" in output

    for marker in markers.values():
        assert marker not in output


def test_json_formatter_filters_celery_task_args_and_kwargs() -> None:
    markers = [
        "P3CELERY_ARG_RAW_21",
        "P3CELERY_KWARG_RAW_22",
    ]

    record = _record(
        logger_name="celery.app.trace",
        message="Task failed",
        data={
            "name": "synthetic.task",
            "args": f"('{markers[0]}',)",
            "kwargs": (
                "{'authorization': "
                f"'{markers[1]}'"
                "}"
            ),
            "description": "raised unexpected",
        },
    )

    output = JsonLogFormatter().format(
        record
    )

    payload = json.loads(
        output
    )

    assert payload["data"]["args"] == "[Filtered]"
    assert payload["data"]["kwargs"] == "[Filtered]"

    for marker in markers:
        assert marker not in output


def test_real_celery_direct_apply_stdout_filters_task_kwargs() -> None:
    markers = [
        "P3CELERY_REAL_AUTH_RAW_31",
        "P3CELERY_REAL_COOKIE_RAW_32",
        "P3CELERY_REAL_PASSWORD_RAW_33",
        "P3CELERY_REAL_APIKEY_RAW_34",
    ]

    child = r"""
from apps.worker.app.worker import celery

@celery.task(
    name="p3.centralized.logging.regression"
)
def fail(**kwargs):
    del kwargs
    raise RuntimeError(
        "P3 centralized logging regression failure"
    )

result = fail.apply(
    kwargs={
        "authorization": "P3CELERY_REAL_AUTH_RAW_31",
        "cookie": "P3CELERY_REAL_COOKIE_RAW_32",
        "password": "P3CELERY_REAL_PASSWORD_RAW_33",
        "api_key": "P3CELERY_REAL_APIKEY_RAW_34",
    },
    throw=False,
)

print(
    "CELERY_RESULT_STATE="
    + str(result.state)
)
"""

    env = os.environ.copy()

    env.update(
        {
            "APP_ENV": "development",
            "DEBUG": "false",
            "DATABASE_URL": (
                "sqlite:///./p3-centralized-log-test.db"
            ),
            "SECRET_KEY": (
                "p3-centralized-logging-regression-"
                "secret-key-not-production"
            ),
            "SENTRY_DSN": "",
            "SENTRY_REQUIRED": "false",
            "LOG_JSON": "true",
        }
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            child,
        ],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert completed.returncode == 0
    assert "CELERY_RESULT_STATE=FAILURE" in completed.stdout
    assert "[Filtered]" in completed.stdout

    for marker in markers:
        assert marker not in completed.stdout


def test_promtail_keeps_correlation_fields_out_of_labels() -> None:
    content = (
        ROOT
        / "infra/logging/promtail-config.yml"
    ).read_text(
        encoding="utf-8"
    )

    assert "request_id: request_id" in content
    assert "path: path" in content

    labels = content.split(
        "      - labels:\n",
        1,
    )[1]

    label_names = {
        line.strip()
        for line in labels.splitlines()
        if line.strip()
    }

    assert "request_id:" not in label_names
    assert "path:" not in label_names

    assert "level:" in label_names
    assert "logger:" in label_names
    assert "status_code:" in label_names


def test_grafana_admin_password_has_no_default_fallback() -> None:
    content = (
        ROOT
        / "infra/logging/docker-compose.observability.yml"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "${GRAFANA_ADMIN_PASSWORD:?"
        "GRAFANA_ADMIN_PASSWORD is required}"
        in content
    )

    assert (
        "GRAFANA_ADMIN_PASSWORD:-CHANGE_ME"
        not in content
    )


def test_logging_readme_documents_mandatory_grafana_password() -> None:
    content = (
        ROOT
        / "infra/logging/README-centralized-logging.md"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "`GRAFANA_ADMIN_PASSWORD` is mandatory"
        in content
    )

    assert (
        "there is no default production password"
        in content
    )
