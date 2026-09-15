from __future__ import annotations

from datetime import timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


@pytest.fixture
def security_module(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite+pysqlite:///:memory:",
    )
    monkeypatch.setenv(
        "SECRET_KEY",
        "jwt-test-secret-key-value-at-least-32-bytes",
    )
    monkeypatch.setenv(
        "APP_ENV",
        "test",
    )
    monkeypatch.setenv(
        "JWT_ALGORITHM",
        "HS256",
    )

    from apps.api.app import config as config_module

    config_module.get_settings.cache_clear()

    test_settings = config_module.get_settings()

    monkeypatch.setattr(
        config_module,
        "settings",
        test_settings,
    )

    from apps.api.app import security as security_module

    monkeypatch.setattr(
        security_module,
        "settings",
        test_settings,
    )

    security_module._jwt_verification_key.cache_clear()

    yield security_module

    security_module._jwt_verification_key.cache_clear()
    config_module.get_settings.cache_clear()


def test_hs256_round_trip(
    security_module,
    monkeypatch,
):
    monkeypatch.setattr(
        security_module.settings,
        "jwt_algorithm",
        "HS256",
    )
    monkeypatch.setattr(
        security_module.settings,
        "secret_key",
        "hs256-test-secret-key-value-at-least-32-bytes",
    )

    token = security_module.create_access_token(
        subject="hs256-user",
    )

    assert (
        security_module.get_subject_from_token(token)
        == "hs256-user"
    )


def test_rs256_round_trip_with_existing_private_key_contract(
    security_module,
    monkeypatch,
):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    monkeypatch.setattr(
        security_module.settings,
        "jwt_algorithm",
        "RS256",
    )
    monkeypatch.setattr(
        security_module.settings,
        "secret_key",
        private_pem,
    )

    token = security_module.create_access_token(
        subject="rs256-user",
    )

    assert (
        security_module.get_subject_from_token(token)
        == "rs256-user"
    )

    verification_key = (
        security_module._jwt_verification_key(
            "RS256",
            private_pem,
        )
    )

    assert b"BEGIN PUBLIC KEY" in verification_key


def test_expired_access_token_is_rejected(
    security_module,
    monkeypatch,
):
    monkeypatch.setattr(
        security_module.settings,
        "jwt_algorithm",
        "HS256",
    )
    monkeypatch.setattr(
        security_module.settings,
        "secret_key",
        "expired-token-test-secret-at-least-32-bytes",
    )

    token = security_module.create_access_token(
        subject="expired-user",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(
        ValueError,
        match="Invalid or expired token",
    ):
        security_module.get_subject_from_token(token)


def test_malformed_access_token_is_rejected(
    security_module,
    monkeypatch,
):
    monkeypatch.setattr(
        security_module.settings,
        "jwt_algorithm",
        "HS256",
    )
    monkeypatch.setattr(
        security_module.settings,
        "secret_key",
        "malformed-token-test-secret-at-least-32-bytes",
    )

    with pytest.raises(
        ValueError,
        match="Invalid or expired token",
    ):
        security_module.get_subject_from_token(
            "not-a-jwt",
        )
