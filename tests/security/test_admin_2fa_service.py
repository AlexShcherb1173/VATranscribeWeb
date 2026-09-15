from apps.api.app.services.admin_2fa_service import (
    generate_recovery_code,
    generate_totp_code,
    generate_totp_secret,
    hash_recovery_code,
    verify_recovery_code,
    verify_totp_code,
)


def test_totp_code_verification_accepts_current_window():
    secret = generate_totp_secret()
    code = generate_totp_code(secret, for_time=1_700_000_000)
    assert verify_totp_code(secret, code, now=1_700_000_000, window=0)
    assert not verify_totp_code(secret, "000000", now=1_700_000_000, window=0)


def test_recovery_code_hash_is_verifiable_and_not_plaintext():
    code = generate_recovery_code()
    encoded = hash_recovery_code(code, salt="fixedsalt")
    assert code not in encoded
    assert verify_recovery_code(code, encoded)
    assert verify_recovery_code(code.lower(), encoded)
    assert not verify_recovery_code("WRONG-CODE", encoded)
