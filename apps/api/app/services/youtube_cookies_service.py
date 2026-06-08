from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.config import get_settings
from apps.api.app.models import User, UserYoutubeCookies

COOKIE_FORMAT_NETSCAPE = "netscape"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _settings():
    return get_settings()


def _fernet() -> Fernet:
    settings = _settings()
    key = (settings.youtube_cookies_encryption_key or "").strip()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YouTube cookies encryption is not configured",
        )

    try:
        return Fernet(key.encode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YouTube cookies encryption key is invalid",
        ) from exc


def _encrypt_cookie_text(cookie_text: str) -> str:
    encrypted = _fernet().encrypt(cookie_text.encode("utf-8"))
    return encrypted.decode("ascii")


def _decrypt_cookie_text(encrypted_cookie_blob: str) -> str:
    try:
        decrypted = _fernet().decrypt(encrypted_cookie_blob.encode("ascii"))
    except InvalidToken as exc:
        raise RuntimeError("Unable to decrypt user YouTube cookies") from exc
    return decrypted.decode("utf-8")


def validate_netscape_cookie_text(cookie_text: str) -> None:
    normalized = cookie_text.replace("\r\n", "\n").replace("\r", "\n")
    non_empty_lines = [line for line in normalized.split("\n") if line.strip()]

    if not non_empty_lines:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="YouTube cookies file is empty",
        )

    data_lines = [line for line in non_empty_lines if not line.lstrip().startswith("#")]
    if not data_lines:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="YouTube cookies file does not contain cookie records",
        )

    for line in data_lines:
        parts = line.split("\t")
        if len(parts) != 7:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only Netscape cookies.txt format is supported",
            )

    if not any("youtube" in line.lower() or "google" in line.lower() for line in data_lines):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cookies file does not look like YouTube/Google cookies",
        )


def _get_row(db: Session, user_id: str) -> UserYoutubeCookies | None:
    stmt = select(UserYoutubeCookies).where(UserYoutubeCookies.user_id == user_id)
    return db.scalar(stmt)


def get_youtube_cookies_status(db: Session, user: User) -> dict[str, object | None]:
    row = _get_row(db, user.id)
    if row is None or row.deleted_at is not None or not row.encrypted_cookie_blob:
        return {
            "configured": False,
            "source_filename": None,
            "cookie_format": None,
            "size_bytes": None,
            "updated_at": None,
        }

    return {
        "configured": True,
        "source_filename": row.source_filename,
        "cookie_format": row.cookie_format,
        "size_bytes": row.size_bytes,
        "updated_at": row.updated_at,
    }


def upsert_youtube_cookies(
    db: Session,
    user: User,
    *,
    content: bytes,
    source_filename: str | None,
) -> UserYoutubeCookies:
    settings = _settings()
    if len(content) > settings.youtube_cookies_max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="YouTube cookies file is too large",
        )

    try:
        cookie_text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="YouTube cookies file must be UTF-8 text",
        ) from exc

    validate_netscape_cookie_text(cookie_text)

    now = _utcnow()
    checksum = hashlib.sha256(content).hexdigest()
    encrypted_blob = _encrypt_cookie_text(cookie_text)

    row = _get_row(db, user.id)
    if row is None:
        row = UserYoutubeCookies(user_id=user.id)

    row.encrypted_cookie_blob = encrypted_blob
    row.cookie_format = COOKIE_FORMAT_NETSCAPE
    row.source_filename = source_filename
    row.checksum_sha256 = checksum
    row.size_bytes = len(content)
    row.deleted_at = None
    row.updated_at = now

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_youtube_cookies(db: Session, user: User) -> bool:
    row = _get_row(db, user.id)
    if row is None:
        return False

    db.delete(row)
    db.commit()
    return True


def get_active_youtube_cookies_text_for_user(db: Session, user_id: str | None) -> str | None:
    if not user_id:
        return None

    row = _get_row(db, user_id)
    if row is None or row.deleted_at is not None or not row.encrypted_cookie_blob:
        return None

    return _decrypt_cookie_text(row.encrypted_cookie_blob)


def create_temp_youtube_cookies_file_for_user(
    db: Session,
    *,
    user_id: str | None,
    job_id: str,
) -> Path | None:
    cookie_text = get_active_youtube_cookies_text_for_user(db, user_id)
    if not cookie_text:
        return None

    temp_dir = _settings().youtube_cookies_temp_dir
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{job_id}.cookies.txt"
    temp_path.write_text(cookie_text, encoding="utf-8", newline="\n")

    try:
        temp_path.chmod(0o600)
    except OSError:
        pass

    return temp_path


def delete_temp_youtube_cookies_file(path: Path | None) -> None:
    if path is None:
        return

    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
