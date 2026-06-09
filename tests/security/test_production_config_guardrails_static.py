from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_settings_declares_production_environment_guardrails():
    text = read("apps/api/app/config.py")

    assert 'app_env: str = Field("development", alias="APP_ENV")' in text
    assert 'debug: bool = Field(True, alias="DEBUG")' in text
    assert 'expose_api_docs: bool = Field(True, alias="EXPOSE_API_DOCS")' in text
    assert '@model_validator(mode="after")' in text
    assert 'def validate_environment_guardrails' in text
    assert 'def _validate_production_settings' in text


def test_production_rejects_unsafe_debug_docs_and_secret_key():
    text = read("apps/api/app/config.py")

    assert 'APP_ENV=production requires DEBUG=false' in text
    assert 'APP_ENV=production requires EXPOSE_API_DOCS=false' in text
    assert 'SECRET_KEY must be at least 32 characters in production' in text
    assert 'SECRET_KEY must not use a default/change-me value' in text


def test_production_validates_cors_origins():
    text = read("apps/api/app/config.py")

    assert 'CORS_ORIGINS must not be empty in production' in text
    assert "origin must use https" in text
    assert "origin must not use localhost/private dev host" in text
    assert "must not contain '*'" in text


def test_production_validates_jwt_and_cookie_policy():
    text = read("apps/api/app/config.py")

    assert 'JWT_ALGORITHM must be HS256 or RS256' in text
    assert 'ACCESS_TOKEN_EXPIRE_MINUTES must be <= 15 in production' in text
    assert 'REFRESH_TOKEN_EXPIRE_DAYS must be <= 30 in production' in text
    assert 'COOKIE_SECURE must be true in production' in text
    assert 'COOKIE_HTTPONLY must be true in production' in text
    assert 'COOKIE_DOMAIN is required in production' in text


def test_fastapi_docs_are_controlled_by_settings():
    text = read("apps/api/app/main.py")

    assert 'docs_url=settings.docs_url' in text
    assert 'redoc_url=settings.redoc_url' in text
    assert 'openapi_url=settings.openapi_url' in text
    assert "docs_url='/docs'" not in text
    assert "redoc_url='/redoc'" not in text
    assert "openapi_url='/openapi.json'" not in text


def test_jwt_algorithm_comes_from_settings():
    text = read("apps/api/app/security.py")

    assert 'algorithm=settings.jwt_algorithm' in text
    assert 'algorithms=[settings.jwt_algorithm]' in text
    assert 'ALGORITHM = "HS256"' not in text


def test_env_examples_document_safe_production_defaults():
    dev_env = read(".env.example")
    prod_env = read(".env.production.example")

    assert "EXPOSE_API_DOCS=true" in dev_env
    assert "JWT_ALGORITHM=HS256" in dev_env
    assert "COOKIE_SECURE=false" in dev_env

    assert "APP_ENV=production" in prod_env
    assert "DEBUG=false" in prod_env
    assert "EXPOSE_API_DOCS=false" in prod_env
    assert "CORS_ORIGINS=https://vatranscribe.ru,https://app.vatranscribe.ru,https://admin.vatranscribe.ru" in prod_env
    assert "ACCESS_TOKEN_EXPIRE_MINUTES=15" in prod_env
    assert "REFRESH_TOKEN_EXPIRE_DAYS=30" in prod_env
    assert "COOKIE_SECURE=true" in prod_env
    assert "COOKIE_HTTPONLY=true" in prod_env
    assert "COOKIE_DOMAIN=.vatranscribe.ru" in prod_env
