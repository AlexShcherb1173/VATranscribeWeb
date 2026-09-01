from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_lf(path: str) -> None:
    data = (ROOT / path).read_bytes()
    assert bytes([13, 10]) not in data, f"CRLF line endings found in {path}"


def test_p3_04_live_validation_scripts_exist_and_are_lf_safe():
    scripts = [
        "infra/deploy/validate-monitoring-live.sh",
        "infra/deploy/validate-alert-delivery.sh",
        "infra/deploy/validate-sentry-test-event.sh",
        "infra/deploy/validate-request-id-live.sh",
    ]
    for script in scripts:
        content = read(script)
        assert content.startswith("#!/usr/bin/env bash")
        assert "set -euo pipefail" in content
        assert "/opt/vatranscribe/secrets/.env.runtime" in content
        assert "Do not" in content or "DO NOT" in content
        assert_lf(script)


def test_monitoring_live_validator_checks_uptime_targets():
    content = read("infra/deploy/validate-monitoring-live.sh")
    assert "PUBLIC_MARKETING_ORIGIN" in content
    assert "PUBLIC_APP_ORIGIN" in content
    assert "PUBLIC_API_ORIGIN" in content
    assert "/api/v1/health/live" in content
    assert "/api/v1/health/ready" in content
    assert "UPTIME_PROVIDER" in content
    assert "UPTIME_ALERT_CHANNELS" in content


def test_alert_delivery_validator_supports_telegram_and_email_without_printing_tokens():
    content = read("infra/deploy/validate-alert-delivery.sh")
    assert "TELEGRAM_ALERT_BOT_TOKEN" in content
    assert "TELEGRAM_ALERT_CHAT_ID" in content
    assert "SMTP_HOST" in content
    assert "SMTP_PASSWORD" in content
    assert "smtplib" in content
    assert "Do not echo tokens" in content


def test_sentry_test_event_validator_uses_runtime_secret_and_sentry_sdk():
    content = read("infra/deploy/validate-sentry-test-event.sh")
    assert "SENTRY_DSN" in content
    assert "sentry_sdk.init" in content
    assert "capture_message" in content
    assert "SENTRY_TEST_EVENT_ID" in content
    assert "send_default_pii=False" in content
    assert "RELEASE_VERSION" in content


def test_request_id_validator_checks_header_and_log_search_marker():
    content = read("infra/deploy/validate-request-id-live.sh")
    assert "X-Request-ID" in content
    assert "REQUEST_ID_HEADER" in content
    assert "/api/v1/health/live" in content
    assert "RESPONSE contains" not in content
    assert "Response contains" in content
    assert "Loki/Grafana" in content
    assert "LOG_SEARCH_MODE" in content
    assert "CORRELATION_REQUEST_ID" in content
    assert 'REQUEST_ID_MODEL="CLIENT_ID_PRESERVED"' in content
    assert 'REQUEST_ID_MODEL="EDGE_GENERATED"' in content
    assert "docker ps" in content
    assert "com.docker.compose.service=api" in content
    assert "com.docker.compose.service=web" in content
    assert "docker logs" in content
    assert "DOCKER_LOG_SINCE" in content
    assert "REQUEST_ID_DOCKER_CORRELATION_OK" in content
    assert "REQUEST_ID_LIVE_VERIFICATION_OK" in content


def test_worker_celery_logging_is_owned_by_application_json_formatter():
    content = read("apps/worker/app/worker.py")

    assert "from celery import Celery, signals" in content

    signal_index = content.index("@signals.setup_logging.connect")
    celery_index = content.index("celery = Celery(")

    hook = content[signal_index:celery_index]

    assert signal_index < celery_index
    assert "def configure_celery_logging(**_: object) -> None:" in hook
    assert "configure_logging(settings)" in hook
    assert "Keep Celery worker logs on the application JSON formatter." in hook

def test_frontend_sentry_sdk_and_build_contract_are_wired():
    package = read("apps/web/package.json")
    sentry = read("apps/web/src/shared/observability/sentry.ts")
    error_boundary = read("apps/web/src/shared/ui/ErrorBoundary.tsx")
    dockerfile = read("infra/docker/web.Dockerfile")

    assert '"@sentry/react": "10.71.0"' in package

    assert 'import * as Sentry from "@sentry/react";' in sentry
    assert "window.Sentry" not in sentry
    assert "Sentry.init({" in sentry
    assert "Sentry.browserTracingIntegration()" in sentry
    assert "environment: env.sentryEnvironment" in sentry
    assert "release: env.sentryRelease" in sentry
    assert "tracesSampleRate: env.sentryTracesSampleRate" in sentry
    assert "sendDefaultPii: false" in sentry
    assert "Sentry.captureException(error)" in sentry
    assert 'window.addEventListener("error"' not in sentry
    assert 'window.addEventListener("unhandledrejection"' not in sentry

    assert (
        'import { captureFrontendException } '
        'from "@/shared/observability/sentry";'
    ) in error_boundary
    assert "captureFrontendException(error);" in error_boundary

    sentry_build_keys = [
        "VITE_SENTRY_DSN",
        "VITE_SENTRY_ENVIRONMENT",
        "VITE_SENTRY_RELEASE",
        "VITE_SENTRY_TRACES_SAMPLE_RATE",
    ]

    for key in sentry_build_keys:
        assert f"ARG {key}" in dockerfile
        assert f"ENV {key}=${{{key}}}" in dockerfile

def test_p3_04_docs_and_evidence_templates_exist():
    docs = [
        "infra/monitoring/monitoring-apm-logs-activation-checklist.md",
        "infra/monitoring/monitoring-apm-logs-evidence-template.md",
        "infra/monitoring/uptime-kuma-production-checks.md",
        "infra/monitoring/alert-delivery-check.md",
        "infra/monitoring/sentry-test-event.md",
        "infra/monitoring/request-id-log-search-check.md",
        "docs/deployment/monitoring-apm-logs-activation.md",
        "docs/architecture/stage-4-p3-04-monitoring-apm-logs-activation.md",
    ]
    corpus = ""
    for doc in docs:
        content = read(doc).lower()
        assert "/opt/vatranscribe/secrets/.env.runtime" in content
        assert "do not" in content
        corpus += "\n" + content
    for marker in ["sentry", "telegram", "email", "request_id", "loki", "grafana"]:
        assert marker in corpus, f"{marker} missing from P3-04 monitoring docs"


def test_release_checklist_includes_p3_04_gate():
    content = read("docs/release/p3-production-activation-checklist.md")
    assert "## P3-04 Monitoring / APM / logs activation" in content
    assert "validate-monitoring-live.sh" in content
    assert "validate-alert-delivery.sh" in content
    assert "validate-sentry-test-event.sh" in content
    assert "validate-request-id-live.sh" in content
    assert "monitoring-apm-logs-evidence" in content
    assert "P3-04 Monitoring / APM / centralized logging live evidence" not in content


def test_gitignore_blocks_monitoring_evidence_artifacts():
    content = read(".gitignore")
    assert "monitoring-apm-logs-evidence*.md" in content
    assert "*.sentry-evidence.txt" in content
    assert "*.request-id-evidence.txt" in content
    assert "*.monitoring-evidence.txt" in content
    assert "uptime-kuma-export*.json" in content
