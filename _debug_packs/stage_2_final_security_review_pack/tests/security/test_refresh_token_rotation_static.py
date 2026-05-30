from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_route_exists(text: str, route: str) -> None:
    single_quote = f"@router.post('{route}'"
    double_quote = f'@router.post("{route}"'

    assert single_quote in text or double_quote in text


def test_auth_router_has_refresh_logout_endpoints():
    text = read("apps/api/app/routers/auth.py")

    assert_route_exists(text, "/refresh")
    assert_route_exists(text, "/logout")
    assert_route_exists(text, "/logout-all")


def test_login_returns_refresh_token():
    text = read("apps/api/app/routers/auth.py")

    assert "create_refresh_token_for_user" in text
    assert "refresh_token=refresh_token" in text


def test_refresh_rotates_refresh_token():
    text = read("apps/api/app/services/refresh_token_service.py")

    assert "old_token.is_revoked = True" in text
    assert "create_refresh_token_for_user" in text


def test_refresh_tokens_model_exists():
    text = read("apps/api/app/models.py")

    assert "class RefreshToken(Base):" in text
    assert '__tablename__ = "refresh_tokens"' in text
