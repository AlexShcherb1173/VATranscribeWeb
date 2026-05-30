from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import User
from apps.api.app.schemas import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
)
from apps.api.app.security import create_access_token
from apps.api.app.services.account_bootstrap import ensure_user_profile, ensure_user_quota
from apps.api.app.services.auth_service import get_password_hash, verify_password
from apps.api.app.services.refresh_token_service import (
    create_refresh_token_for_user,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(prefix='/auth', tags=['Auth'])


def normalize_email(email: str) -> str:
    return email.strip().lower()


def ensure_account_defaults(db: Session, user: User) -> None:
    try:
        ensure_user_profile(db, user)
        ensure_user_quota(db, user)
        db.commit()
    except IntegrityError:
        db.rollback()
        ensure_user_profile(db, user)
        ensure_user_quota(db, user)
        db.commit()


@router.post('/register', response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    email = normalize_email(payload.email)

    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='User with this email already exists.',
        )

    user = User(
        email=email,
        password_hash=get_password_hash(payload.password),
        is_active=True,
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='User with this email already exists.',
        ) from exc

    db.refresh(user)
    ensure_account_defaults(db, user)
    db.refresh(user)

    return user


@router.post('/login', response_model=TokenResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = normalize_email(payload.email)

    user = db.scalar(select(User).where(User.email == email))

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid email or password.',
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='User is inactive.',
        )

    ensure_account_defaults(db, user)
    db.refresh(user)

    refresh_token, _ = create_refresh_token_for_user(db, user)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=refresh_token,
        token_type='bearer',
    )


@router.post('/refresh', response_model=TokenResponse)
def refresh_tokens(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user, new_refresh_token, _ = rotate_refresh_token(db, payload.refresh_token)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=new_refresh_token,
        token_type='bearer',
    )


@router.post('/logout', response_model=LogoutResponse)
def logout_user(
    payload: LogoutRequest,
    db: Session = Depends(get_db),
) -> LogoutResponse:
    if payload.refresh_token:
        revoke_refresh_token(db, payload.refresh_token)
        db.commit()

    return LogoutResponse(ok=True, detail='Logged out')


@router.post('/logout-all', response_model=LogoutResponse)
def logout_all_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LogoutResponse:
    revoked_count = revoke_all_user_refresh_tokens(db, current_user)
    db.commit()

    return LogoutResponse(
        ok=True,
        detail=f'Revoked refresh tokens: {revoked_count}',
    )


@router.get('/me', response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
