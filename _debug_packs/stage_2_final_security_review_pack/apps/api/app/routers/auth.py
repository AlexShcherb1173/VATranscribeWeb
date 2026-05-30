from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
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
from apps.api.app.security_foundation.privacy import mask_email
from apps.api.app.services.account_bootstrap import ensure_user_profile, ensure_user_quota
from apps.api.app.services.audit_service import record_audit_event
from apps.api.app.services.auth_service import get_password_hash, verify_password
from apps.api.app.services.consent_service import record_user_consents, validate_required_consents
from apps.api.app.services.refresh_token_service import (
    create_refresh_token_for_user,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


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


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    email = normalize_email(payload.email)

    try:
        required_documents = validate_required_consents(
            db=db,
            accepted_legal_documents=payload.accepted_legal_documents,
        )
    except HTTPException:
        record_audit_event(
            db=db,
            request=request,
            action="auth.register_failed",
            entity_type="User",
            meta={
                "email_mask": mask_email(email),
                "reason": "required_legal_consents_missing_or_invalid",
            },
        )
        db.commit()
        raise

    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        record_audit_event(
            db=db,
            request=request,
            action="auth.register_failed",
            entity_type="User",
            meta={
                "email_mask": mask_email(email),
                "reason": "email_already_exists",
            },
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists.",
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
        record_audit_event(
            db=db,
            request=request,
            action="auth.register_failed",
            entity_type="User",
            meta={
                "email_mask": mask_email(email),
                "reason": "integrity_error",
            },
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists.",
        ) from exc

    db.refresh(user)
    ensure_account_defaults(db, user)
    db.refresh(user)

    consent_rows = record_user_consents(
        db=db,
        user=user,
        request=request,
        documents=required_documents,
    )

    record_audit_event(
        db=db,
        request=request,
        action="legal.consents_accepted",
        actor_user_id=str(user.id),
        entity_type="User",
        entity_id=str(user.id),
        meta={
            "documents": [
                {
                    "document_type": row.document_type,
                    "document_version": row.document_version,
                }
                for row in consent_rows
            ],
        },
    )

    record_audit_event(
        db=db,
        request=request,
        action="auth.register_success",
        actor_user_id=str(user.id),
        entity_type="User",
        entity_id=str(user.id),
        meta={
            "email_mask": mask_email(user.email),
        },
    )
    db.commit()

    return user


@router.post("/login", response_model=TokenResponse)
def login_user(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    email = normalize_email(payload.email)

    user = db.scalar(select(User).where(User.email == email))

    if user is None or not verify_password(payload.password, user.password_hash):
        record_audit_event(
            db=db,
            request=request,
            action="auth.login_failed",
            entity_type="User",
            meta={
                "email_mask": mask_email(email),
                "reason": "invalid_credentials",
            },
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        record_audit_event(
            db=db,
            request=request,
            action="auth.login_failed",
            actor_user_id=str(user.id),
            entity_type="User",
            entity_id=str(user.id),
            meta={
                "email_mask": mask_email(email),
                "reason": "inactive_user",
            },
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive.",
        )

    ensure_account_defaults(db, user)
    db.refresh(user)

    refresh_token, token_row = create_refresh_token_for_user(db, user)

    record_audit_event(
        db=db,
        request=request,
        action="auth.login_success",
        actor_user_id=str(user.id),
        entity_type="RefreshToken",
        entity_id=str(token_row.id),
        meta={
            "email_mask": mask_email(user.email),
        },
    )

    db.commit()

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    try:
        user, new_refresh_token, token_row = rotate_refresh_token(db, payload.refresh_token)
    except HTTPException:
        record_audit_event(
            db=db,
            request=request,
            action="auth.refresh_failed",
            entity_type="RefreshToken",
            meta={
                "reason": "invalid_revoked_or_expired",
            },
        )
        db.commit()
        raise

    record_audit_event(
        db=db,
        request=request,
        action="auth.refresh_success",
        actor_user_id=str(user.id),
        entity_type="RefreshToken",
        entity_id=str(token_row.id),
    )

    db.commit()

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post("/logout", response_model=LogoutResponse)
def logout_user(
    payload: LogoutRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> LogoutResponse:
    revoked = False

    if payload.refresh_token:
        revoked = revoke_refresh_token(db, payload.refresh_token)

    record_audit_event(
        db=db,
        request=request,
        action="auth.logout",
        entity_type="RefreshToken",
        meta={
            "revoked": revoked,
        },
    )

    db.commit()

    return LogoutResponse(ok=True, detail="Logged out")


@router.post("/logout-all", response_model=LogoutResponse)
def logout_all_user_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LogoutResponse:
    revoked_count = revoke_all_user_refresh_tokens(db, current_user)

    record_audit_event(
        db=db,
        request=request,
        action="auth.logout_all",
        actor_user_id=str(current_user.id),
        entity_type="User",
        entity_id=str(current_user.id),
        meta={
            "revoked_count": revoked_count,
        },
    )

    db.commit()

    return LogoutResponse(
        ok=True,
        detail=f"Revoked refresh tokens: {revoked_count}",
    )


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
