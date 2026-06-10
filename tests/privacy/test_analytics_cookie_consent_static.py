from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cookie_consent_categories_and_version_are_defined():
    env_example = read(".env.example")
    web_consent = read("apps/web/src/shared/cookies/consent.ts")
    marketing_banner = read("apps/marketing/src/components/CookieConsent.astro")

    assert "COOKIE_CONSENT_REQUIRED=true" in env_example
    assert "COOKIE_CONSENT_VERSION=2026-06-10" in env_example
    assert "necessary" in web_consent
    assert "analytics" in web_consent
    assert "marketing" in web_consent
    assert "vatranscribe.cookieConsent" in web_consent
    assert "localStorage" in web_consent
    assert "data-cookie-category=\"analytics\"" in marketing_banner
    assert "data-cookie-category=\"marketing\"" in marketing_banner


def test_analytics_is_disabled_by_default_and_env_driven():
    for path in [".env.example", ".env.production.example"]:
        content = read(path)
        assert "ANALYTICS_PROVIDER=disabled" in content
        assert "YANDEX_METRIKA_ID=" in content
        assert "GA4_MEASUREMENT_ID=" in content
        assert "VITE_ANALYTICS_PROVIDER=disabled" in content
        assert "PUBLIC_ANALYTICS_PROVIDER=disabled" in content

    analytics = read("apps/web/src/shared/analytics/analytics.ts")
    assert "initConsentAwareAnalytics" in analytics
    assert "hasConsentFor(\"analytics\"" in analytics
    assert "mc.yandex.ru/metrika/tag.js" in analytics
    assert "googletagmanager.com/gtag/js" in analytics
    assert "123456" not in analytics
    assert "G-" not in analytics


def test_marketing_and_web_surfaces_include_cookie_banner():
    app_providers = read("apps/web/src/app/providers/AppProviders.tsx")
    base_layout = read("apps/marketing/src/layouts/BaseLayout.astro")

    assert "CookieConsentBanner" in app_providers
    assert "CookieConsent" in base_layout
    assert "Admin" not in read("apps/marketing/src/components/CookieConsent.astro")


def test_legal_docs_describe_cookie_consent_gate():
    cookie_policy = read("docs/legal/cookie-policy.md")
    deployment = read("docs/deployment/analytics-cookie-consent-core-web-vitals.md")

    assert "Analytics storage is disabled by default" in cookie_policy
    assert "marketing consent" in cookie_policy.lower()
    assert "No tracking IDs are hardcoded" in deployment
    assert "no analytics network request" in deployment.lower()
