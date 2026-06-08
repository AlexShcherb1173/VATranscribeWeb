from __future__ import annotations

import secrets

from fastapi import HTTPException, Request, Response, status

from apps.api.app.config import settings


AUTH_COOKIE_PATH = f"{settings.api_prefix}/auth"
CSRF_COOKIE_PATH = "/"


def _cookie_domain() -> str | None:
    return settings.cookie_domain or None


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=AUTH_COOKIE_PATH,
        domain=_cookie_domain(),
        secure=settings.cookie_secure,
        httponly=settings.cookie_httponly,
        samesite=settings.cookie_samesite,
    )


def set_csrf_cookie(response: Response) -> str:
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=CSRF_COOKIE_PATH,
        domain=_cookie_domain(),
        secure=settings.cookie_secure,
        httponly=False,
        samesite=settings.cookie_samesite,
    )
    return csrf_token


def set_auth_cookies(response: Response, refresh_token: str) -> None:
    set_refresh_cookie(response, refresh_token)
    set_csrf_cookie(response)


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=AUTH_COOKIE_PATH,
        domain=_cookie_domain(),
        secure=settings.cookie_secure,
        httponly=settings.cookie_httponly,
        samesite=settings.cookie_samesite,
    )
    response.delete_cookie(
        key=settings.csrf_cookie_name,
        path=CSRF_COOKIE_PATH,
        domain=_cookie_domain(),
        secure=settings.cookie_secure,
        httponly=False,
        samesite=settings.cookie_samesite,
    )


def get_refresh_token_from_cookie(request: Request) -> str:
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh cookie is missing",
        )
    return refresh_token


def validate_csrf(request: Request) -> None:
    cookie_token = request.cookies.get(settings.csrf_cookie_name)
    header_token = request.headers.get(settings.csrf_header_name)

    if not cookie_token or not header_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token is missing",
        )

    if not secrets.compare_digest(cookie_token, header_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token is invalid",
        )
