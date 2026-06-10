from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_env_contains_monitoring_and_logging_controls():
    env = read(".env.production.example")
    assert "MONITORING_REQUIRED=true" in env
    assert "MONITORING_RELEASE_CHECKLIST_ACK=false" in env
    assert "UPTIME_PROVIDER=uptime-kuma" in env
    assert "APM_PROVIDER=sentry" in env
    assert "SENTRY_REQUIRED=true" in env
    assert "CENTRAL_LOGGING_REQUIRED=true" in env
    assert "CENTRAL_LOGGING_PROVIDER=loki" in env
    assert "LOKI_RETENTION_DAYS=14" in env
    assert "REQUEST_ID_HEADER=X-Request-ID" in env


def test_config_has_production_monitoring_guardrails():
    config = read("apps/api/app/config.py")
    assert "monitoring_required" in config
    assert "monitoring_release_checklist_ack" in config
    assert "sentry_required" in config
    assert "central_logging_required" in config
    assert "MONITORING_RELEASE_CHECKLIST_ACK must be true" in config
    assert "SENTRY_DSN is required" in config
    assert "CENTRAL_LOGGING_PROVIDER must not be disabled" in config


def test_api_worker_and_frontend_sentry_hooks_exist():
    api_obs = read("apps/api/app/observability.py")
    worker = read("apps/worker/app/worker.py")
    frontend = read("apps/web/src/shared/observability/sentry.ts")
    main = read("apps/web/src/main.tsx")
    assert "FastApiIntegration" in api_obs
    assert "CeleryIntegration" in api_obs
    assert 'init_sentry(settings, service="worker")' in worker
    assert "VITE_SENTRY_DSN" in read("apps/web/src/shared/config/env.ts")
    assert "initFrontendObservability" in frontend
    assert "initFrontendObservability();" in main


def test_request_id_and_nginx_json_logs_are_enabled():
    main = read("apps/api/app/main.py")
    nginx = read("infra/docker/nginx.prod.conf.template")
    assert "request_id_and_access_log_middleware" in main
    assert "X-Request-ID" in main
    assert "request_logger.info" in main
    assert "log_format vatranscribe_json" in nginx
    assert "access_log /var/log/nginx/access.log vatranscribe_json" in nginx
    assert "proxy_set_header X-Request-ID $request_id" in nginx


def test_loki_promtail_grafana_overlay_exists():
    overlay = read("infra/logging/docker-compose.observability.yml")
    loki = read("infra/logging/loki-config.yml")
    promtail = read("infra/logging/promtail-config.yml")
    assert "grafana/loki" in overlay
    assert "grafana/promtail" in overlay
    assert "grafana/grafana" in overlay
    assert "retention_period: 336h" in loki
    assert "docker_sd_configs" in promtail
    assert "request_id" in promtail


def test_uptime_alerts_runbook_and_docs_exist():
    uptime = read("infra/monitoring/uptime-kuma-checks.yml")
    checklist = read("infra/monitoring/monitoring-release-checklist.md")
    runbook = read("infra/monitoring/monitoring-runbook.md")
    docs = read("docs/deployment/monitoring-logging.md")
    assert "https://vatranscribe.ru" in uptime
    assert "https://api.vatranscribe.ru/api/v1/health/live" in uptime
    assert "alert_channels" in uptime
    assert "MONITORING_RELEASE_CHECKLIST_ACK=true" in docs
    assert "request_id" in runbook
    assert "Sentry" in checklist


def test_deploy_validation_and_monitoring_smoke_are_wired():
    validate = read("infra/deploy/validate-production-secrets.sh")
    render = read("infra/deploy/render-runtime-env.sh")
    deploy = read("infra/deploy/deploy.sh")
    smoke = read("infra/deploy/monitoring-smoke.sh")
    assert "MONITORING_REQUIRED" in validate
    assert "require_bool_value MONITORING_RELEASE_CHECKLIST_ACK true" in validate
    assert "require_secret_non_placeholder SENTRY_DSN" in validate
    assert "CENTRAL_LOGGING_PROVIDER" in validate
    assert "VITE_SENTRY_DSN" in render
    assert "monitoring-smoke.sh" in deploy
    assert "/api/v1/health/ready" in smoke
