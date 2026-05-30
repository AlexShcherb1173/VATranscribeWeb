from __future__ import annotations

from pathlib import Path

ROOT = Path(r"D:\DevProject\PythonProject\VATranscribeWeb")


def write_text(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def patch_models() -> None:
    path = ROOT / "apps/api/app/models.py"
    text = path.read_text(encoding="utf-8")

    if "    JSON," not in text:
        text = text.replace(
            "    Integer,\n    String,",
            "    Integer,\n    JSON,\n    String,",
        )

    if "class AuditLog(Base):" not in text:
        audit_model = '''
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    actor_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    entity_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    meta_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    ip_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    user_agent_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    actor: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[actor_user_id],
    )

'''
        marker = "\nclass Plan(Base):"
        if marker not in text:
            raise RuntimeError("Could not find class Plan(Base) insertion point in models.py")
        text = text.replace(marker, "\n" + audit_model + "class Plan(Base):")

    path.write_text(text, encoding="utf-8")


def write_audit_service() -> None:
    write_text(
        "apps/api/app/services/audit_service.py",
        '''
from __future__ import annotations

import hashlib
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from apps.api.app.models import AuditLog


def _hash_optional(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _get_client_ip(request: Request | None) -> str | None:
    if request is None:
        return None

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    if request.client:
        return request.client.host

    return None


def _get_user_agent(request: Request | None) -> str | None:
    if request is None:
        return None
    return request.headers.get("user-agent")


def record_audit_event(
    db: Session,
    action: str,
    request: Request | None = None,
    actor_user_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> AuditLog:
    event = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        meta_json=meta or {},
        ip_hash=_hash_optional(_get_client_ip(request)),
        user_agent_hash=_hash_optional(_get_user_agent(request)),
    )
    db.add(event)
    db.flush()
    return event
''',
    )


def write_auth_router() -> None:
    write_text(
        "apps/api/app/routers/auth.py",
        '''
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
''',
    )


def write_billing_router() -> None:
    write_text(
        "apps/api/app/routers/billing.py",
        '''
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import User
from apps.api.app.schemas import (
    BillingOverviewResponse,
    BillingUpgradeRequest,
    BillingUpgradeResponse,
)
from apps.api.app.services.audit_service import record_audit_event
from apps.api.app.services.billing_service import get_billing_overview, upgrade_user_plan

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/overview", response_model=BillingOverviewResponse)
def billing_overview(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BillingOverviewResponse:
    result = get_billing_overview(db, current_user)

    record_audit_event(
        db=db,
        request=request,
        action="billing.overview_viewed",
        actor_user_id=str(current_user.id),
        entity_type="User",
        entity_id=str(current_user.id),
    )
    db.commit()

    return BillingOverviewResponse(**result)


@router.post("/upgrade", response_model=BillingUpgradeResponse)
def billing_upgrade(
    payload: BillingUpgradeRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BillingUpgradeResponse:
    record_audit_event(
        db=db,
        request=request,
        action="billing.upgrade_requested",
        actor_user_id=str(current_user.id),
        entity_type="User",
        entity_id=str(current_user.id),
        meta={
            "plan_code": payload.plan_code,
            "billing_period": payload.billing_period,
        },
    )

    try:
        current_plan, subscription, quota = upgrade_user_plan(
            db=db,
            user=current_user,
            plan_code=payload.plan_code,
            billing_period=payload.billing_period,
        )
    except ValueError as exc:
        record_audit_event(
            db=db,
            request=request,
            action="billing.upgrade_failed",
            actor_user_id=str(current_user.id),
            entity_type="User",
            entity_id=str(current_user.id),
            meta={
                "plan_code": payload.plan_code,
                "billing_period": payload.billing_period,
                "reason": str(exc),
            },
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    record_audit_event(
        db=db,
        request=request,
        action="billing.upgrade_succeeded",
        actor_user_id=str(current_user.id),
        entity_type="Subscription",
        entity_id=str(subscription.id),
        meta={
            "plan_code": payload.plan_code,
            "billing_period": payload.billing_period,
            "subscription_id": str(subscription.id),
            "plan_id": str(current_plan.id),
        },
    )
    db.commit()

    return BillingUpgradeResponse(
        current_plan=current_plan,
        subscription=subscription,
        quota=quota,
    )
''',
    )


def write_tests() -> None:
    write_text(
        "tests/security/test_audit_logs_static.py",
        '''
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_audit_log_model_exists():
    text = read("apps/api/app/models.py")
    assert "class AuditLog(Base):" in text
    assert '__tablename__ = "audit_logs"' in text
    assert "meta_json" in text
    assert "ip_hash" in text
    assert "user_agent_hash" in text


def test_audit_service_records_audit_event():
    text = read("apps/api/app/services/audit_service.py")
    assert "def record_audit_event(" in text
    assert "AuditLog(" in text
    assert "_get_client_ip" in text
    assert "_get_user_agent" in text


def test_auth_router_writes_audit_events():
    text = read("apps/api/app/routers/auth.py")
    assert "auth.register_success" in text
    assert "auth.register_failed" in text
    assert "auth.login_success" in text
    assert "auth.login_failed" in text
    assert "auth.refresh_success" in text
    assert "auth.refresh_failed" in text
    assert "auth.logout" in text
    assert "auth.logout_all" in text


def test_billing_router_writes_audit_events():
    text = read("apps/api/app/routers/billing.py")
    assert "billing.overview_viewed" in text
    assert "billing.upgrade_requested" in text
    assert "billing.upgrade_succeeded" in text
    assert "billing.upgrade_failed" in text
''',
    )


def write_docs() -> None:
    write_text(
        "docs/security/audit-logs.md",
        '''
# Audit Logs

Stage 2.3 implements audit logging for real auth and billing flows.

## Database table

Audit events are stored in `audit_logs`.

Tracked fields:

- actor_user_id
- action
- entity_type
- entity_id
- meta_json
- ip_hash
- user_agent_hash
- created_at

## Auth events

Implemented actions:

- auth.register_success
- auth.register_failed
- auth.login_success
- auth.login_failed
- auth.refresh_success
- auth.refresh_failed
- auth.logout
- auth.logout_all

## Billing events

Implemented actions:

- billing.overview_viewed
- billing.upgrade_requested
- billing.upgrade_succeeded
- billing.upgrade_failed

## Admin actions

Backend admin routers are not implemented yet.

When admin backend endpoints are added, every admin mutation must create an audit event:

- admin.user.updated
- admin.user.blocked
- admin.subscription.updated
- admin.payment.refunded
- admin.plan.updated
- admin.quota.updated
- admin.file.deleted
- admin.legal_document.published
- admin.security_event.resolved

## Privacy note

IP address and user-agent are stored only as SHA-256 hashes.
Email values in metadata must be masked.
''',
    )

    write_text(
        "docs/security/admin-audit-actions.md",
        '''
# Admin Audit Actions

Admin backend endpoints are planned but not implemented yet.

When implemented, admin actions must follow this rule:

Every admin mutation must write one audit event before returning success.

## Required metadata

- admin actor user id
- action
- entity type
- entity id
- minimal metadata
- IP hash
- user-agent hash

## Planned actions

- admin.user.viewed
- admin.user.updated
- admin.user.blocked
- admin.subscription.updated
- admin.payment.refunded
- admin.plan.created
- admin.plan.updated
- admin.quota.updated
- admin.file.deleted
- admin.legal_document.created
- admin.legal_document.published
- admin.privacy_request.processed
- admin.security_event.resolved
''',
    )


def main() -> None:
    if not ROOT.exists():
        raise RuntimeError(f"Project root not found: {ROOT}")

    patch_models()
    write_audit_service()
    write_auth_router()
    write_billing_router()
    write_tests()
    write_docs()

    print("Stage 2.3 audit logs patch completed.")
    print("")
    print("Next:")
    print("docker compose build api")
    print("docker compose up -d api")
    print("docker compose exec api python -m pip install pytest")
    print("docker compose exec api python -m pytest tests/security tests/privacy")
    print("docker compose exec db psql -U postgres -d vatranscribe -c \"select action, actor_user_id, entity_type, entity_id, created_at from audit_logs order by created_at desc limit 20;\"")


if __name__ == "__main__":
    main()