from __future__ import annotations


class PasswordPolicyError(ValueError):
    pass


def validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise PasswordPolicyError('Password must contain at least 8 characters')

    if password.lower() == password:
        raise PasswordPolicyError('Password must contain at least one uppercase letter')

    if password.upper() == password:
        raise PasswordPolicyError('Password must contain at least one lowercase letter')

    if not any(ch.isdigit() for ch in password):
        raise PasswordPolicyError('Password must contain at least one digit')


def is_password_acceptable(password: str) -> bool:
    try:
        validate_password_strength(password)
    except PasswordPolicyError:
        return False
    return True
