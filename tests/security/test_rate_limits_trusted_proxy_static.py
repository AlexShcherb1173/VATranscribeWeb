from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_redis_backed_limiter_exists():
    text = read("apps/api/app/security_foundation/rate_limits.py")

    assert "class RedisBackedRateLimiter" in text
    assert "Redis.from_url" in text
    assert "Rate limit backend unavailable" in text
    assert "class ConfiguredRateLimiter" in text


def test_client_ip_uses_trusted_proxy_cidrs():
    text = read("apps/api/app/security_foundation/rate_limits.py")

    assert "def get_client_ip(" in text
    assert "trusted_proxy_cidrs" in text
    assert "is_trusted_proxy_ip" in text
    assert "_is_public_forwarded_client_ip" in text
    assert 'request.headers.get("x-forwarded-for")' in text
    assert "return forwarded_for.split" not in text


def test_settings_expose_rate_limit_policy():
    text = read("apps/api/app/config.py")

    assert "rate_limit_backend" in text
    assert "rate_limit_redis_url" in text
    assert "trusted_proxy_cidrs" in text
    assert "rate_limit_general_api_per_minute" in text
    assert "rate_limit_auth_per_minute" in text
    assert "rate_limit_auth_strict_per_minute" in text
    assert "rate_limit_upload_per_minute" in text
    assert "rate_limit_download_per_minute" in text
    assert "rate_limit_analyze_per_minute" in text


def test_production_requires_redis_rate_limit_backend():
    text = read("apps/api/app/config.py")

    assert 'rate_limit_backend != "redis"' in text
    assert "RATE_LIMIT_FAIL_OPEN must be false in production" in text
    assert "TRUSTED_PROXY_CIDRS" in text


def test_audit_and_consent_use_safe_client_ip_helper():
    audit = read("apps/api/app/services/audit_service.py")
    consent = read("apps/api/app/services/consent_service.py")

    for text in (audit, consent):
        assert "from apps.api.app.security_foundation.rate_limits import get_client_ip" in text
        assert "return get_client_ip(request)" in text
        assert "return forwarded_for.split" not in text


def test_api_routes_use_configured_rate_limit_policy():
    auth = read("apps/api/app/routers/auth.py")
    downloads = read("apps/api/app/routers/downloads.py")
    uploads = read("apps/api/app/routers/uploads.py")
    jobs = read("apps/api/app/routers/jobs.py")
    main = read("apps/api/app/main.py")

    assert "settings.rate_limit_auth_strict_per_minute" in auth
    assert "settings.rate_limit_auth_per_minute" in auth
    assert "settings.rate_limit_analyze_per_minute" in downloads
    assert "settings.rate_limit_download_per_minute" in downloads
    assert "settings.rate_limit_upload_per_minute" in uploads
    assert "settings.rate_limit_download_per_minute" in jobs
    assert "api_rate_limit_middleware" in main
    assert "settings.rate_limit_general_api_per_minute" in main


def test_env_examples_document_rate_limit_settings():
    for path in [".env.example", ".env.production.example"]:
        text = read(path)
        assert "RATE_LIMIT_BACKEND=" in text
        assert "RATE_LIMIT_REDIS_URL=" in text
        assert "TRUSTED_PROXY_CIDRS=" in text
        assert "RATE_LIMIT_GENERAL_API_PER_MINUTE=120" in text
        assert "RATE_LIMIT_AUTH_PER_MINUTE=10" in text
        assert "RATE_LIMIT_AUTH_STRICT_PER_MINUTE=5" in text
