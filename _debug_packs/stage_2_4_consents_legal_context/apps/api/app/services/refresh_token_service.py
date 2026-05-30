from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.config import settings
from apps.api.app.models import RefreshToken, User
from apps.api.app.security_foundation.token_rotation import (
    generate_refresh_token,
    hash_refresh_token,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_refresh_token_for_user(
    db: Session,
    user: User,
) -> tuple[str, RefreshToken]:
    raw_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_token)

    token_row = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        is_revoked=False,
        expires_at=utcnow() + timedelta(days=settings.refresh_token_expire_days),
    )

    db.add(token_row)
    db.flush()

    return raw_token, token_row


def get_active_refresh_token_or_401(
    db: Session,
    raw_token: str,
) -> RefreshToken:
    token_hash = hash_refresh_token(raw_token)

    token_row = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )

    if token_row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid refresh token',
        )

    if token_row.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Refresh token has been revoked',
        )

    if token_row.expires_at <= utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Refresh token has expired',
        )

    return token_row


def rotate_refresh_token(
    db: Session,
    raw_token: str,
) -> tuple[User, str, RefreshToken]:
    old_token = get_active_refresh_token_or_401(db, raw_token)

    user = db.get(User, old_token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not found or inactive',
        )

    old_token.is_revoked = True
    old_token.revoked_at = utcnow()

    new_raw_token, new_token_row = create_refresh_token_for_user(db, user)

    return user, new_raw_token, new_token_row


def revoke_refresh_token(
    db: Session,
    raw_token: str,
) -> bool:
    try:
        token_row = get_active_refresh_token_or_401(db, raw_token)
    except HTTPException:
        return False

    token_row.is_revoked = True
    token_row.revoked_at = utcnow()
    db.flush()

    return True


def revoke_all_user_refresh_tokens(
    db: Session,
    user: User,
) -> int:
    token_rows = list(
        db.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.is_revoked.is_(False),
            )
        )
    )

    now = utcnow()
    for token_row in token_rows:
        token_row.is_revoked = True
        token_row.revoked_at = now

    db.flush()

    return len(token_rows)
