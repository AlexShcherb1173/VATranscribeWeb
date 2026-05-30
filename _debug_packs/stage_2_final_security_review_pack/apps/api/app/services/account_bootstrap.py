from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.app.models import User, UserProfile, UserQuota


DEFAULT_STORAGE_BYTES_LIMIT = 10 * 1024 * 1024 * 1024  # 10 GB
DEFAULT_TRANSCRIPTION_SECONDS_LIMIT = 36_000           # 10 hours
DEFAULT_JOBS_COUNT_LIMIT = 500


def ensure_user_profile(db: Session, user: User) -> UserProfile:
    """
    Возвращает профиль пользователя, создавая его при отсутствии.

    Функция идемпотентна:
    - если профиль уже существует, просто возвращает его;
    - если профиль создаётся параллельно в другом запросе, корректно
      обрабатывает IntegrityError и перечитывает запись из БД.
    """
    profile = db.scalar(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    if profile is not None:
        return profile

    profile = UserProfile(
        id=str(uuid.uuid4()),
        user_id=user.id,
    )
    db.add(profile)

    try:
        db.commit()
        db.refresh(profile)
        return profile
    except IntegrityError:
        db.rollback()
        existing_profile = db.scalar(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        if existing_profile is None:
            raise
        return existing_profile


def ensure_user_quota(db: Session, user: User) -> UserQuota:
    """
    Возвращает квоту пользователя, создавая её при отсутствии.

    Функция идемпотентна и устойчива к гонкам:
    - сначала ищет существующую запись;
    - если записи нет, пытается создать;
    - если другая транзакция успела вставить ту же запись раньше,
      ловит IntegrityError, делает rollback и перечитывает запись.
    """
    quota = db.scalar(
        select(UserQuota).where(UserQuota.user_id == user.id)
    )
    if quota is not None:
        return quota

    quota = UserQuota(
        id=str(uuid.uuid4()),
        user_id=user.id,
        storage_bytes_used=0,
        transcription_seconds_used=0,
        jobs_count_used=0,
        storage_bytes_limit=DEFAULT_STORAGE_BYTES_LIMIT,
        transcription_seconds_limit=DEFAULT_TRANSCRIPTION_SECONDS_LIMIT,
        jobs_count_limit=DEFAULT_JOBS_COUNT_LIMIT,
    )
    db.add(quota)

    try:
        db.commit()
        db.refresh(quota)
        return quota
    except IntegrityError:
        db.rollback()
        existing_quota = db.scalar(
            select(UserQuota).where(UserQuota.user_id == user.id)
        )
        if existing_quota is None:
            raise
        return existing_quota