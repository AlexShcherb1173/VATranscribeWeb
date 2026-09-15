from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from jwt import InvalidTokenError

from apps.api.app.config import settings


@lru_cache(maxsize=8)
def _jwt_verification_key(
    algorithm: str,
    secret_key: str,
) -> str | bytes:
    if algorithm != "RS256":
        return secret_key

    private_key = serialization.load_pem_private_key(
        secret_key.encode("utf-8"),
        password=None,
    )

    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def get_subject_from_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            _jwt_verification_key(
                settings.jwt_algorithm,
                settings.secret_key,
            ),
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise ValueError("Invalid or expired token") from exc

    subject = payload.get("sub")
    if not subject:
        raise ValueError("Token payload does not contain subject")

    return str(subject)
