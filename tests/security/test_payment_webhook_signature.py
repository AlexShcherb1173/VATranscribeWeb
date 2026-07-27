from apps.api.app.services.payment_event_service import (
    compute_webhook_signature,
    verify_webhook_signature,
)


def test_payment_webhook_signature_verification_accepts_plain_and_prefixed_hash():
    secret = "test-secret"
    body = b'{"event_id":"evt_1"}'
    digest = compute_webhook_signature(secret, body)

    assert verify_webhook_signature(secret, body, digest)
    assert verify_webhook_signature(secret, body, f"sha256={digest}")


def test_payment_webhook_signature_verification_rejects_missing_or_wrong_hash():
    secret = "test-secret"
    body = b'{"event_id":"evt_1"}'

    assert not verify_webhook_signature(secret, body, None)
    assert not verify_webhook_signature(secret, body, "wrong")
    assert not verify_webhook_signature("other-secret", body, compute_webhook_signature(secret, body))
