from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_backend_uses_httponly_refresh_cookie_and_csrf_double_submit():
    text = read("apps/api/app/security_foundation/auth_cookies.py")

    assert "set_refresh_cookie" in text
    assert "key=settings.refresh_cookie_name" in text
    assert "httponly=settings.cookie_httponly" in text
    assert "secure=settings.cookie_secure" in text
    assert "samesite=settings.cookie_samesite" in text
    assert "set_csrf_cookie" in text
    assert "httponly=False" in text
    assert "def validate_csrf" in text
    assert "secrets.compare_digest" in text


def test_auth_routes_use_cookie_refresh_not_request_body_refresh_token():
    text = read("apps/api/app/routers/auth.py")

    assert "set_auth_cookies(response, refresh_token)" in text
    assert "set_auth_cookies(response, new_refresh_token)" in text
    assert "get_refresh_token_from_cookie(request)" in text
    assert "validate_csrf(request)" in text
    assert "clear_auth_cookies(response)" in text
    assert "payload.refresh_token" not in text
    assert "refresh_token=refresh_token" not in text
    assert "refresh_token=new_refresh_token" not in text


def test_token_response_no_longer_exposes_refresh_token():
    text = read("apps/api/app/schemas.py")
    token_response = text.split("class TokenResponse(BaseModel):", 1)[1].split("class LogoutResponse", 1)[0]

    assert "access_token: str" in token_response
    assert "token_type: str" in token_response
    assert "refresh_token" not in token_response


def test_frontend_access_token_is_memory_only():
    text = read("apps/web/src/shared/auth/token.ts")

    assert "let accessToken: string | null = null" in text
    assert "localStorage" not in text
    assert "sessionStorage" not in text


def test_frontend_api_client_uses_credentials_csrf_and_refresh_retry():
    text = read("apps/web/src/shared/api/client.ts")

    assert "withCredentials: true" in text
    assert "X-CSRF-Token" in read("apps/web/src/shared/auth/csrf.ts")
    assert "getCsrfToken" in text
    assert "refreshAccessToken" in text
    assert 'post<TokenResponse>(AUTH_REFRESH_PATH)' in text
    assert "setAccessToken(response.data.access_token)" in text


def test_logout_calls_backend_before_clearing_memory_token():
    auth_api = read("apps/web/src/features/auth/api/auth.ts")
    topbar = read("apps/web/src/widgets/topbar/Topbar.tsx")

    assert "export async function logoutUser" in auth_api
    assert 'apiClient.post("/auth/logout")' in auth_api
    assert "await logoutUser()" in topbar
    assert "destroySession()" in topbar


def test_nginx_has_temporary_csp_baseline():
    text = read("infra/docker/nginx.conf")

    assert "Content-Security-Policy" in text
    assert "frame-ancestors 'none'" in text
    assert "base-uri 'self'" in text
