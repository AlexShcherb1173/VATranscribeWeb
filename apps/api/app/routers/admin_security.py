from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.app.database import get_db
from apps.api.app.dependencies import require_admin_2fa, require_admin_user
from apps.api.app.models import User
from apps.api.app.schemas.admin_security import (
    AdminSecurityCheckResponse,
    AdminTwoFactorConfirmResponse,
    AdminTwoFactorDisableRequest,
    AdminTwoFactorRecoveryCodesResponse,
    AdminTwoFactorSetupResponse,
    AdminTwoFactorStatusResponse,
    AdminTwoFactorVerifyRequest,
)
from apps.api.app.services.admin_2fa_service import (
    begin_admin_2fa_setup,
    confirm_admin_2fa_setup,
    consume_recovery_code,
    disable_admin_2fa,
    get_admin_2fa,
    recovery_codes_remaining,
    rotate_admin_recovery_codes,
    verify_admin_totp,
)
from apps.api.app.services.audit_service import record_audit_event

router = APIRouter(prefix="/admin/security", tags=["admin-security"])


@router.get("/2fa/status", response_model=AdminTwoFactorStatusResponse)
def get_admin_2fa_status(
    current_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminTwoFactorStatusResponse:
    row = get_admin_2fa(db, current_user)
    return AdminTwoFactorStatusResponse(
        enabled=bool(row and row.enabled and row.encrypted_totp_secret),
        confirmed_at=row.confirmed_at if row else None,
        recovery_codes_remaining=recovery_codes_remaining(db, current_user),
    )


@router.post("/2fa/setup", response_model=AdminTwoFactorSetupResponse)
def setup_admin_2fa(
    request: Request,
    current_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminTwoFactorSetupResponse:
    _, secret, otpauth_url = begin_admin_2fa_setup(db, current_user)
    record_audit_event(
        db,
        action="admin.2fa_setup_started",
        request=request,
        actor_user_id=current_user.id,
        entity_type="AdminTwoFactor",
        entity_id=current_user.id,
    )
    db.commit()
    return AdminTwoFactorSetupResponse(secret=secret, otpauth_url=otpauth_url)


@router.post("/2fa/confirm", response_model=AdminTwoFactorConfirmResponse)
def confirm_admin_2fa(
    payload: AdminTwoFactorVerifyRequest,
    request: Request,
    current_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminTwoFactorConfirmResponse:
    try:
        _, recovery_codes = confirm_admin_2fa_setup(db, current_user, payload.code)
    except ValueError as exc:
        record_audit_event(
            db,
            action="admin.2fa_confirm_failed",
            request=request,
            actor_user_id=current_user.id,
            entity_type="AdminTwoFactor",
            entity_id=current_user.id,
            meta={"reason": str(exc)},
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    record_audit_event(
        db,
        action="admin.2fa_enabled",
        request=request,
        actor_user_id=current_user.id,
        entity_type="AdminTwoFactor",
        entity_id=current_user.id,
        meta={"recovery_codes_count": len(recovery_codes)},
    )
    db.commit()
    return AdminTwoFactorConfirmResponse(enabled=True, recovery_codes=recovery_codes)


@router.post("/2fa/disable", response_model=AdminTwoFactorStatusResponse)
def disable_admin_2fa_endpoint(
    payload: AdminTwoFactorDisableRequest,
    request: Request,
    current_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminTwoFactorStatusResponse:
    verified = False
    if payload.code:
        verified = verify_admin_totp(db, current_user, payload.code)
    if not verified and payload.recovery_code:
        verified = consume_recovery_code(db, current_user, payload.recovery_code)
    if not verified:
        record_audit_event(
            db,
            action="admin.2fa_disable_failed",
            request=request,
            actor_user_id=current_user.id,
            entity_type="AdminTwoFactor",
            entity_id=current_user.id,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Valid 2FA code or recovery code required")

    row = disable_admin_2fa(db, current_user)
    record_audit_event(
        db,
        action="admin.2fa_disabled",
        request=request,
        actor_user_id=current_user.id,
        entity_type="AdminTwoFactor",
        entity_id=current_user.id,
    )
    db.commit()
    return AdminTwoFactorStatusResponse(enabled=False, confirmed_at=row.confirmed_at, recovery_codes_remaining=0)


@router.post("/2fa/recovery-codes/rotate", response_model=AdminTwoFactorRecoveryCodesResponse)
def rotate_admin_2fa_recovery_codes(
    payload: AdminTwoFactorVerifyRequest,
    request: Request,
    current_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
) -> AdminTwoFactorRecoveryCodesResponse:
    if not verify_admin_totp(db, current_user, payload.code):
        record_audit_event(
            db,
            action="admin.2fa_recovery_codes_rotate_failed",
            request=request,
            actor_user_id=current_user.id,
            entity_type="AdminRecoveryCode",
            entity_id=current_user.id,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Valid 2FA code required")

    codes = rotate_admin_recovery_codes(db, current_user)
    record_audit_event(
        db,
        action="admin.2fa_recovery_codes_rotated",
        request=request,
        actor_user_id=current_user.id,
        entity_type="AdminRecoveryCode",
        entity_id=current_user.id,
        meta={"recovery_codes_count": len(codes)},
    )
    db.commit()
    return AdminTwoFactorRecoveryCodesResponse(recovery_codes=codes)


@router.get("/check", response_model=AdminSecurityCheckResponse)
def check_admin_2fa_gate(
    _: User = Depends(require_admin_2fa),
) -> AdminSecurityCheckResponse:
    return AdminSecurityCheckResponse()
