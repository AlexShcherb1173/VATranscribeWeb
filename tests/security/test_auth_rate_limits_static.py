from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_rate_limit_helper_has_stable_key_builder():
    text = read("apps/api/app/security_foundation/rate_limits.py")

    assert "def get_client_ip(" in text
    assert "def stable_hash(" in text
    assert "def build_rate_limit_key(" in text
    assert "class InMemoryRateLimiter" in text


def test_auth_router_imports_rate_limiter():
    text = read("apps/api/app/routers/auth.py")

    assert "from apps.api.app.security_foundation.rate_limits import build_rate_limit_key, rate_limiter" in text
    assert "def check_auth_rate_limit(" in text
    assert "auth.rate_limited" in text


def test_register_endpoint_is_rate_limited():
    text = read("apps/api/app/routers/auth.py")

    register_index = text.index('@router.post("/register"')
    login_index = text.index('@router.post("/login"')
    register_block = text[register_index:login_index]

    assert 'action="auth.register"' in register_block
    assert 'build_rate_limit_key("auth:register", request)' in register_block
    assert "limit=5" in register_block
    assert "window_seconds=600" in register_block


def test_login_endpoint_is_rate_limited():
    text = read("apps/api/app/routers/auth.py")

    login_index = text.index('@router.post("/login"')
    refresh_index = text.index('@router.post("/refresh"')
    login_block = text[login_index:refresh_index]

    assert 'action="auth.login"' in login_block
    assert 'build_rate_limit_key("auth:login", request, subject=email)' in login_block
    assert "limit=10" in login_block
    assert "window_seconds=300" in login_block


def test_refresh_endpoint_is_rate_limited():
    text = read("apps/api/app/routers/auth.py")

    refresh_index = text.index('@router.post("/refresh"')
    logout_index = text.index('@router.post("/logout"')
    refresh_block = text[refresh_index:logout_index]

    assert 'action="auth.refresh"' in refresh_block
    assert 'build_rate_limit_key("auth:refresh", request)' in refresh_block
    assert "limit=30" in refresh_block
    assert "window_seconds=300" in refresh_block
