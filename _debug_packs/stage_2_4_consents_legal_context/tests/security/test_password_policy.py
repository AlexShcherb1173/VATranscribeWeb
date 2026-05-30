import pytest

from apps.api.app.security_foundation.password_policy import PasswordPolicyError, validate_password_strength


def test_password_policy_accepts_strong_password():
    validate_password_strength('StrongPass123')


def test_password_policy_rejects_short_password():
    with pytest.raises(PasswordPolicyError):
        validate_password_strength('A1b')
