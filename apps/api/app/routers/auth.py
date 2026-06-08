from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.app.config import settings
from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import User
from apps.api.app.schemas import (
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    TokenResponse,
    UserRead,
)
from apps.api.app.security import create_access_token
from apps.api.app.security_foundation.auth_cookies import (
    clear_auth_cookies,
    get_refresh_token_from_cookie,
    set_auth_cookies,
    validate_csrf,
)
from apps.api.app.security_foundation.privacy import mask_email
from apps.api.app.security_foundation.rate_limits import build_rate_limit_key, rate_limiter
from apps.api.app.security_foundation.password_policy import PasswordPolicyError, validate_password_strength
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


def check_auth_rate_limit(
    db: Session,
    request: Request,
    action: str,
    key: str,
    limit: int,
    window_seconds: int,
    email: str | None = None,
) -> None:
    try:
        rate_limiter.check(
            key=key,
            limit=limit,
            window_seconds=window_seconds,
        )
    except HTTPException as exc:
        if exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            meta = {
                "limited_action": action,
                "limit": limit,
                "window_seconds": window_seconds,
            }

            if email:
                meta["email_mask"] = mask_email(email)

            record_audit_event(
                db=db,
                request=request,
                action="auth.rate_limited",
                entity_type="RateLimit",
                meta=meta,
            )
            db.commit()

        raise

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    email = normalize_email(payload.email)

    check_auth_rate_limit(
        db=db,
        request=request,
        action="auth.register",
        key=build_rate_limit_key("auth:register", request),
        limit=5,
        window_seconds=600,
        email=email,
    )

    try:
        validate_password_strength(payload.password)
    except PasswordPolicyError as exc:
        record_audit_event(
            db=db,
            request=request,
            action="auth.register_failed",
            entity_type="User",
            meta={
                "email_mask": mask_email(email),
                "reason": "password_policy_failed",
                "policy_error": str(exc),
            },
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

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


@router.post("/login", response_model=TokenResponse, response_model_exclude_none=True)
def login_user(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    email = normalize_email(payload.email)

    check_auth_rate_limit(
        db=db,
        request=request,
        action="auth.login",
        key=build_rate_limit_key("auth:login", request, subject=email),
        limit=10,
        window_seconds=300,
        email=email,
    )

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

    set_auth_cookies(response, refresh_token)

    db.commit()

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        token_type="bearer",
    )


@router.post("/refresh", response_model=TokenResponse, response_model_exclude_none=True)
def refresh_tokens(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    validate_csrf(request)
    raw_refresh_token = get_refresh_token_from_cookie(request)

    check_auth_rate_limit(
        db=db,
        request=request,
        action="auth.refresh",
        key=build_rate_limit_key("auth:refresh", request),
        limit=30,
        window_seconds=300,
    )

    try:
        user, new_refresh_token, token_row = rotate_refresh_token(db, raw_refresh_token)
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
        clear_auth_cookies(response)
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

    set_auth_cookies(response, new_refresh_token)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        token_type="bearer",
    )


@router.post("/logout", response_model=LogoutResponse)
def logout_user(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> LogoutResponse:
    validate_csrf(request)
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    revoked = False

    if refresh_token:
        revoked = revoke_refresh_token(db, refresh_token)

    clear_auth_cookies(response)

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
    response: Response,
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

    clear_auth_cookies(response)

    db.commit()

    return LogoutResponse(
        ok=True,
        detail=f"Revoked refresh tokens: {revoked_count}",
    )


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


