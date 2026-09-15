from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_core_web_vitals_targets_are_configured():
    env_example = read(".env.example")
    web_cwv = read("apps/web/src/shared/core-web-vitals/coreWebVitals.ts")
    checklist = read("docs/performance/core-web-vitals-checklist.md")

    assert "CORE_WEB_VITALS_ENABLED=true" in env_example
    assert "CORE_WEB_VITALS_LCP_TARGET_MS=2500" in env_example
    assert "CORE_WEB_VITALS_INP_TARGET_MS=200" in env_example
    assert "CORE_WEB_VITALS_CLS_TARGET=0.1" in env_example
    assert "largest-contentful-paint" in web_cwv
    assert "layout-shift" in web_cwv
    assert "LCP" in checklist
    assert "INP" in checklist
    assert "CLS" in checklist


def test_core_web_vitals_reports_after_analytics_consent_only():
    web_cwv = read("apps/web/src/shared/core-web-vitals/coreWebVitals.ts")
    marketing_cwv = read("apps/marketing/src/scripts/coreWebVitals.ts")
    docs = read("docs/deployment/analytics-cookie-consent-core-web-vitals.md")

    assert "hasConsentFor(\"analytics\")" in web_cwv
    assert "trackAnalyticsEvent" in web_cwv
    assert "shouldReportCoreWebVitalsAfterConsent" in marketing_cwv
    assert "Core Web Vitals reporting is allowed only after analytics consent" in docs


def test_backend_config_and_runtime_env_include_analytics_gate():
    config = read("apps/api/app/config.py")
    render = read("infra/deploy/render-runtime-env.sh")
    validate = read("infra/deploy/validate-production-secrets.sh")

    assert "analytics_provider" in config
    assert "cookie_consent_required" in config
    assert "core_web_vitals_lcp_target_ms" in config
    assert "ANALYTICS_PROVIDER" in render
    assert "COOKIE_CONSENT_REQUIRED" in render
    assert "CORE_WEB_VITALS_LCP_TARGET_MS" in render
    assert "COOKIE_CONSENT_REQUIRED" in validate
    assert "ANALYTICS_PROVIDER" in validate
