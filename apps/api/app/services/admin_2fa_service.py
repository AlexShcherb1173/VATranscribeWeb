from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import quote

from cryptography.fernet import Fernet
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from apps.api.app.config import get_settings
from apps.api.app.models import AdminRecoveryCode, AdminTwoFactor, User

TOTP_INTERVAL_SECONDS = 30
TOTP_DIGITS = 6
RECOVERY_HASH_ITERATIONS = 200_000


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fernet() -> Fernet:
    settings = get_settings()
    material = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(material))


def encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")


def normalize_totp_code(code: str) -> str:
    return "".join(ch for ch in (code or "") if ch.isdigit())


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _decode_base32(secret: str) -> bytes:
    normalized = secret.strip().replace(" ", "").upper()
    padding = "=" * ((8 - len(normalized) % 8) % 8)
    return base64.b32decode(normalized + padding, casefold=True)


def generate_totp_code(secret: str, *, for_time: int | None = None, interval: int = TOTP_INTERVAL_SECONDS, digits: int = TOTP_DIGITS) -> str:
    timestamp = int(time.time() if for_time is None else for_time)
    counter = timestamp // interval
    key = _decode_base32(secret)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(binary % (10 ** digits)).zfill(digits)


def verify_totp_code(secret: str, code: str, *, now: int | None = None, window: int = 1) -> bool:
    normalized = normalize_totp_code(code)
    if len(normalized) != TOTP_DIGITS:
        return False

    timestamp = int(time.time() if now is None else now)
    for offset in range(-window, window + 1):
        expected = generate_totp_code(secret, for_time=timestamp + offset * TOTP_INTERVAL_SECONDS)
        if hmac.compare_digest(expected, normalized):
            return True
    return False


def build_otpauth_url(secret: str, *, account_label: str, issuer: str) -> str:
    label = f"{issuer}:{account_label}"
    return (
        "otpauth://totp/"
        f"{quote(label)}?secret={quote(secret)}&issuer={quote(issuer)}"
        f"&algorithm=SHA1&digits={TOTP_DIGITS}&period={TOTP_INTERVAL_SECONDS}"
    )


def generate_recovery_code(byte_length: int = 10) -> str:
    token = secrets.token_urlsafe(byte_length).replace("_", "").replace("-", "")
    return "-".join([token[:5], token[5:10], token[10:15]]).upper()


def hash_recovery_code(code: str, *, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    normalized = code.strip().upper().replace(" ", "")
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        normalized.encode("utf-8"),
        salt.encode("utf-8"),
        RECOVERY_HASH_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${RECOVERY_HASH_ITERATIONS}${salt}${digest}"


def verify_recovery_code(code: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    normalized = code.strip().upper().replace(" ", "")
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        normalized.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(actual, expected)


def get_admin_2fa(db: Session, user: User) -> AdminTwoFactor | None:
    return db.scalar(select(AdminTwoFactor).where(AdminTwoFactor.user_id == user.id))


def get_or_create_admin_2fa(db: Session, user: User) -> AdminTwoFactor:
    row = get_admin_2fa(db, user)
    if row is not None:
        return row
    row = AdminTwoFactor(user_id=user.id, enabled=False)
    db.add(row)
    db.flush()
    return row


def is_admin_2fa_enabled(db: Session, user: User) -> bool:
    if not getattr(user, "is_admin", False):
        return False
    row = get_admin_2fa(db, user)
    return bool(row and row.enabled and row.encrypted_totp_secret)


def recovery_codes_remaining(db: Session, user: User) -> int:
    return int(db.scalar(
        select(func.count(AdminRecoveryCode.id)).where(
            AdminRecoveryCode.user_id == user.id,
            AdminRecoveryCode.used_at.is_(None),
        )
    ) or 0)


def begin_admin_2fa_setup(db: Session, user: User) -> tuple[AdminTwoFactor, str, str]:
    settings = get_settings()
    row = get_or_create_admin_2fa(db, user)
    secret = generate_totp_secret()
    row.encrypted_pending_totp_secret = encrypt_secret(secret)
    row.updated_at = utcnow()
    db.add(row)
    db.flush()
    return row, secret, build_otpauth_url(secret, account_label=user.email, issuer=settings.admin_2fa_issuer)


def _replace_recovery_codes(db: Session, user: User) -> list[str]:
    settings = get_settings()
    db.execute(delete(AdminRecoveryCode).where(AdminRecoveryCode.user_id == user.id))
    plain_codes: list[str] = []
    for _ in range(settings.admin_2fa_recovery_code_count):
        plain = generate_recovery_code(settings.admin_2fa_recovery_code_bytes)
        plain_codes.append(plain)
        db.add(AdminRecoveryCode(
            id=str(uuid.uuid4()),
            user_id=user.id,
            code_hash=hash_recovery_code(plain),
        ))
    return plain_codes


def confirm_admin_2fa_setup(db: Session, user: User, code: str) -> tuple[AdminTwoFactor, list[str]]:
    settings = get_settings()
    row = get_admin_2fa(db, user)
    if row is None or not row.encrypted_pending_totp_secret:
        raise ValueError("Admin 2FA setup has not been started")
    secret = decrypt_secret(row.encrypted_pending_totp_secret)
    if not verify_totp_code(secret, code, window=settings.admin_2fa_totp_window):
        raise ValueError("Invalid two-factor authentication code")
    row.enabled = True
    row.encrypted_totp_secret = row.encrypted_pending_totp_secret
    row.encrypted_pending_totp_secret = None
    row.confirmed_at = utcnow()
    row.disabled_at = None
    row.updated_at = utcnow()
    db.add(row)
    recovery_codes = _replace_recovery_codes(db, user)
    db.flush()
    return row, recovery_codes


def verify_admin_totp(db: Session, user: User, code: str) -> bool:
    settings = get_settings()
    row = get_admin_2fa(db, user)
    if row is None or not row.enabled or not row.encrypted_totp_secret:
        return False
    secret = decrypt_secret(row.encrypted_totp_secret)
    return verify_totp_code(secret, code, window=settings.admin_2fa_totp_window)


def consume_recovery_code(db: Session, user: User, code: str) -> bool:
    rows = db.scalars(
        select(AdminRecoveryCode).where(
            AdminRecoveryCode.user_id == user.id,
            AdminRecoveryCode.used_at.is_(None),
        )
    ).all()
    for row in rows:
        if verify_recovery_code(code, row.code_hash):
            row.used_at = utcnow()
            db.add(row)
            db.flush()
            return True
    return False


def disable_admin_2fa(db: Session, user: User) -> AdminTwoFactor:
    row = get_or_create_admin_2fa(db, user)
    row.enabled = False
    row.encrypted_totp_secret = None
    row.encrypted_pending_totp_secret = None
    row.disabled_at = utcnow()
    row.updated_at = utcnow()
    db.execute(delete(AdminRecoveryCode).where(AdminRecoveryCode.user_id == user.id))
    db.add(row)
    db.flush()
    return row


def rotate_admin_recovery_codes(db: Session, user: User) -> list[str]:
    codes = _replace_recovery_codes(db, user)
    db.flush()
    return codes
