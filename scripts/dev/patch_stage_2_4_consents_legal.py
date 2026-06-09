from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"D:\DevProject\PythonProject\VATranscribeWeb")


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8-sig")


def write_text(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def patch_models() -> None:
    path = ROOT / "apps/api/app/models.py"
    text = path.read_text(encoding="utf-8-sig")

    if "class LegalDocument(Base):" not in text:
        models_block = '''
class LegalDocument(Base):
    __tablename__ = "legal_documents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    document_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class UserConsent(Base):
    __tablename__ = "user_consents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    document_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    accepted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
    )

'''
        marker = "\nclass Plan(Base):"
        if marker not in text:
            raise RuntimeError("Could not find class Plan(Base) insertion point in models.py")
        text = text.replace(marker, "\n" + models_block + "class Plan(Base):")

    path.write_text(text, encoding="utf-8")


def patch_schemas() -> None:
    path = ROOT / "apps/api/app/schemas.py"
    text = path.read_text(encoding="utf-8-sig")

    if "class LegalDocumentAcceptanceRequest(BaseModel):" not in text:
        insert = '''
class LegalDocumentAcceptanceRequest(BaseModel):
    document_type: str = Field(min_length=2, max_length=100)
    document_version: str = Field(min_length=1, max_length=50)
    accepted: bool = True


class LegalDocumentRead(BaseModel):
    id: str
    document_type: str
    version: str
    title: str
    content: str
    is_active: bool
    published_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserConsentRead(BaseModel):
    id: str
    user_id: str
    document_type: str
    document_version: str
    accepted: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ConsentAcceptCurrentRequest(BaseModel):
    accepted: bool = True


class ConsentAcceptCurrentResponse(BaseModel):
    items: list[UserConsentRead] = Field(default_factory=list)


'''
        text = text.replace("class RegisterRequest(BaseModel):", insert + "class RegisterRequest(BaseModel):")

    text = re.sub(
        r"class RegisterRequest\(BaseModel\):\n\s+email: EmailStr\n\s+password: str = Field\(min_length=8, max_length=255\)",
        '''class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)
    accepted_legal_documents: list[LegalDocumentAcceptanceRequest] = Field(default_factory=list)''',
        text,
    )

    path.write_text(text, encoding="utf-8")


def write_legal_document_service() -> None:
    write_text(
        "apps/api/app/services/legal_document_service.py",
        '''
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.models import LegalDocument

REQUIRED_LEGAL_DOCUMENT_TYPES: tuple[str, ...] = (
    "terms",
    "privacy",
    "personal_data",
)

DEFAULT_LEGAL_DOCUMENTS: tuple[dict[str, str], ...] = (
    {
        "document_type": "terms",
        "version": "1.0",
        "title": "Terms of Service",
        "content": "Default Terms of Service placeholder. Replace with final legal text before production.",
    },
    {
        "document_type": "privacy",
        "version": "1.0",
        "title": "Privacy Policy",
        "content": "Default Privacy Policy placeholder. Replace with final legal text before production.",
    },
    {
        "document_type": "personal_data",
        "version": "1.0",
        "title": "Personal Data Processing Consent",
        "content": "Default personal data processing consent placeholder. Replace before production.",
    },
)


def normalize_document_type(document_type: str) -> str:
    return document_type.strip().lower().replace(" ", "_").replace("-", "_")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_default_legal_documents(db: Session) -> None:
    for item in DEFAULT_LEGAL_DOCUMENTS:
        document_type = normalize_document_type(item["document_type"])

        existing = db.scalar(
            select(LegalDocument).where(
                LegalDocument.document_type == document_type,
                LegalDocument.version == item["version"],
            )
        )

        if existing is not None:
            if not existing.is_active:
                existing.is_active = True
            if existing.published_at is None:
                existing.published_at = utcnow()
            continue

        db.add(
            LegalDocument(
                document_type=document_type,
                version=item["version"],
                title=item["title"],
                content=item["content"],
                is_active=True,
                published_at=utcnow(),
            )
        )

    db.flush()


def list_active_legal_documents(db: Session) -> list[LegalDocument]:
    ensure_default_legal_documents(db)

    return list(
        db.scalars(
            select(LegalDocument)
            .where(LegalDocument.is_active.is_(True))
            .order_by(LegalDocument.document_type.asc(), LegalDocument.published_at.desc())
        )
    )


def list_required_active_legal_documents(db: Session) -> list[LegalDocument]:
    ensure_default_legal_documents(db)

    documents: list[LegalDocument] = []

    for document_type in REQUIRED_LEGAL_DOCUMENT_TYPES:
        document = get_current_legal_document(db, document_type)
        documents.append(document)

    return documents


def get_current_legal_document(db: Session, document_type: str) -> LegalDocument:
    ensure_default_legal_documents(db)

    normalized = normalize_document_type(document_type)

    document = db.scalar(
        select(LegalDocument)
        .where(
            LegalDocument.document_type == normalized,
            LegalDocument.is_active.is_(True),
        )
        .order_by(LegalDocument.published_at.desc(), LegalDocument.created_at.desc())
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active legal document '{normalized}' not found",
        )

    return document


class LegalDocumentService:
    def normalize_document_type(self, document_type: str) -> str:
        return normalize_document_type(document_type)


legal_document_service = LegalDocumentService()
''',
    )


def write_consent_service() -> None:
    write_text(
        "apps/api/app/services/consent_service.py",
        '''
from __future__ import annotations

import hashlib
from typing import Any

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.models import LegalDocument, User, UserConsent
from apps.api.app.services.legal_document_service import (
    REQUIRED_LEGAL_DOCUMENT_TYPES,
    list_required_active_legal_documents,
    normalize_document_type,
)


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


def _get_payload_value(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def normalize_acceptance_payload(items: list[Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}

    for item in items:
        document_type = normalize_document_type(str(_get_payload_value(item, "document_type") or ""))
        document_version = str(_get_payload_value(item, "document_version") or "")
        accepted = bool(_get_payload_value(item, "accepted"))

        if not document_type or not document_version:
            continue

        result[document_type] = {
            "document_type": document_type,
            "document_version": document_version,
            "accepted": accepted,
        }

    return result


def validate_required_consents(
    db: Session,
    accepted_legal_documents: list[Any],
) -> list[LegalDocument]:
    required_documents = list_required_active_legal_documents(db)
    accepted_map = normalize_acceptance_payload(accepted_legal_documents)

    missing: list[str] = []
    version_mismatch: list[str] = []

    for document in required_documents:
        item = accepted_map.get(document.document_type)

        if item is None or not item["accepted"]:
            missing.append(document.document_type)
            continue

        if item["document_version"] != document.version:
            version_mismatch.append(
                f"{document.document_type}: expected {document.version}, got {item['document_version']}"
            )

    if missing or version_mismatch:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Required legal documents must be accepted",
                "missing": missing,
                "version_mismatch": version_mismatch,
                "required_document_types": list(REQUIRED_LEGAL_DOCUMENT_TYPES),
            },
        )

    return required_documents


def record_user_consents(
    db: Session,
    user: User,
    request: Request | None,
    documents: list[LegalDocument],
) -> list[UserConsent]:
    ip_hash = _hash_optional(_get_client_ip(request))
    user_agent_hash = _hash_optional(_get_user_agent(request))

    rows: list[UserConsent] = []

    for document in documents:
        row = UserConsent(
            user_id=user.id,
            document_type=document.document_type,
            document_version=document.version,
            accepted=True,
            ip_hash=ip_hash,
            user_agent_hash=user_agent_hash,
        )
        db.add(row)
        rows.append(row)

    db.flush()

    return rows


def accept_current_required_consents(
    db: Session,
    user: User,
    request: Request | None,
) -> list[UserConsent]:
    documents = list_required_active_legal_documents(db)
    return record_user_consents(
        db=db,
        user=user,
        request=request,
        documents=documents,
    )


def list_user_consents(
    db: Session,
    user: User,
) -> list[UserConsent]:
    return list(
        db.scalars(
            select(UserConsent)
            .where(UserConsent.user_id == user.id)
            .order_by(UserConsent.created_at.desc())
        )
    )


class ConsentService:
    def build_consent_record(
        self,
        user_id: int | str,
        document_type: str,
        document_version: str,
        accepted: bool = True,
    ) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "document_type": document_type,
            "document_version": document_version,
            "accepted": accepted,
        }


consent_service = ConsentService()
''',
    )


def write_legal_router() -> None:
    write_text(
        "apps/api/app/routers/legal.py",
        '''
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.database import get_db
from apps.api.app.schemas import LegalDocumentRead
from apps.api.app.services.legal_document_service import (
    get_current_legal_document,
    list_active_legal_documents,
    list_required_active_legal_documents,
)

router = APIRouter(prefix="/legal", tags=["legal"])


@router.get("/documents", response_model=list[LegalDocumentRead])
def list_legal_documents(db: Session = Depends(get_db)) -> list:
    documents = list_active_legal_documents(db)
    db.commit()
    return documents


@router.get("/documents/current", response_model=list[LegalDocumentRead])
def list_current_required_legal_documents(db: Session = Depends(get_db)) -> list:
    documents = list_required_active_legal_documents(db)
    db.commit()
    return documents


@router.get("/documents/{document_type}/current", response_model=LegalDocumentRead)
def read_current_legal_document(
    document_type: str,
    db: Session = Depends(get_db),
):
    document = get_current_legal_document(db, document_type)
    db.commit()
    return document
''',
    )


def write_consents_router() -> None:
    write_text(
        "apps/api/app/routers/consents.py",
        '''
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import User
from apps.api.app.schemas import ConsentAcceptCurrentResponse, UserConsentRead
from apps.api.app.services.audit_service import record_audit_event
from apps.api.app.services.consent_service import (
    accept_current_required_consents,
    list_user_consents,
)

router = APIRouter(prefix="/consents", tags=["consents"])


@router.get("/me", response_model=list[UserConsentRead])
def list_my_consents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    return list_user_consents(db, current_user)


@router.post("/accept-current", response_model=ConsentAcceptCurrentResponse)
def accept_current_consents(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsentAcceptCurrentResponse:
    rows = accept_current_required_consents(
        db=db,
        user=current_user,
        request=request,
    )

    record_audit_event(
        db=db,
        request=request,
        action="legal.consents_accepted",
        actor_user_id=str(current_user.id),
        entity_type="User",
        entity_id=str(current_user.id),
        meta={
            "documents": [
                {
                    "document_type": row.document_type,
                    "document_version": row.document_version,
                }
                for row in rows
            ],
        },
    )

    db.commit()

    return ConsentAcceptCurrentResponse(items=rows)
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
''',
    )


def patch_frontend_types(relative_path: str) -> None:
    path = ROOT / relative_path
    if not path.exists():
        return

    text = path.read_text(encoding="utf-8")

    if "LegalDocumentAcceptance" not in text:
        text = text.replace(
            "export type RegisterRequest = {\n  email: string;\n  password: string;\n};",
            '''export type LegalDocumentAcceptance = {
  document_type: string;
  document_version: string;
  accepted: boolean;
};

export type RegisterRequest = {
  email: string;
  password: string;
  accepted_legal_documents: LegalDocumentAcceptance[];
};''',
        )

    if "refresh_token" not in text:
        text = text.replace(
            "export type TokenResponse = {\n  access_token: string;\n  token_type: string;\n};",
            '''export type TokenResponse = {
  access_token: string;
  refresh_token?: string | null;
  token_type: string;
};''',
        )

    path.write_text(text, encoding="utf-8")


def patch_register_form(relative_path: str) -> None:
    path = ROOT / relative_path
    if not path.exists():
        return

    text = path.read_text(encoding="utf-8")

    if "acceptedLegalDocuments" not in text:
        text = text.replace(
            '  const [errorMessage, setErrorMessage] = useState<string | null>(null);',
            '''  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [acceptedLegalDocuments, setAcceptedLegalDocuments] = useState(false);''',
        )

    text = text.replace(
        "mutationFn: async (payload: { email: string; password: string }) => {",
        "mutationFn: async (payload: { email: string; password: string; accepted_legal_documents: { document_type: string; document_version: string; accepted: boolean }[] }) => {",
    )

    if "Необходимо принять условия" not in text:
        text = text.replace(
            '''    if (password !== confirmPassword) {
      setErrorMessage(t.auth.passwordMismatch);
      return;
    }

    setErrorMessage(null);

    mutation.mutate({
      email: email.trim(),
      password,
    });''',
            '''    if (password !== confirmPassword) {
      setErrorMessage(t.auth.passwordMismatch);
      return;
    }

    if (!acceptedLegalDocuments) {
      setErrorMessage("Необходимо принять условия сервиса и политику конфиденциальности.");
      return;
    }

    setErrorMessage(null);

    mutation.mutate({
      email: email.trim(),
      password,
      accepted_legal_documents: [
        { document_type: "terms", document_version: "1.0", accepted: true },
        { document_type: "privacy", document_version: "1.0", accepted: true },
        { document_type: "personal_data", document_version: "1.0", accepted: true },
      ],
    });''',
        )

    if "Я принимаю условия сервиса" not in text:
        text = text.replace(
            '''      {errorMessage ? (''',
            '''      <label className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/5 p-3 text-xs leading-5 text-slate-300">
        <input
          type="checkbox"
          checked={acceptedLegalDocuments}
          onChange={(event) => setAcceptedLegalDocuments(event.target.checked)}
          className="mt-1 h-4 w-4 rounded border-white/20 bg-slate-950"
        />
        <span>
          Я принимаю условия сервиса, политику конфиденциальности и согласие на обработку персональных данных.
        </span>
      </label>

      {errorMessage ? (''',
        )

    path.write_text(text, encoding="utf-8")


def write_tests() -> None:
    write_text(
        "tests/privacy/test_consents_legal_static.py",
        '''
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_legal_and_consent_models_exist():
    text = read("apps/api/app/models.py")

    assert "class LegalDocument(Base):" in text
    assert '__tablename__ = "legal_documents"' in text
    assert "class UserConsent(Base):" in text
    assert '__tablename__ = "user_consents"' in text


def test_register_request_requires_legal_acceptances():
    text = read("apps/api/app/schemas.py")

    assert "class LegalDocumentAcceptanceRequest(BaseModel):" in text
    assert "accepted_legal_documents" in text


def test_register_validates_required_consents():
    text = read("apps/api/app/routers/auth.py")

    assert "validate_required_consents" in text
    assert "record_user_consents" in text
    assert "legal.consents_accepted" in text


def test_legal_router_exposes_current_documents():
    text = read("apps/api/app/routers/legal.py")

    assert '@router.get("/documents"' in text
    assert '@router.get("/documents/current"' in text
    assert '@router.get("/documents/{document_type}/current"' in text


def test_consents_router_exposes_user_consents_and_accept_current():
    text = read("apps/api/app/routers/consents.py")

    assert '@router.get("/me"' in text
    assert '@router.post("/accept-current"' in text
''',
    )


def write_docs() -> None:
    write_text(
        "docs/privacy/consent-flow.md",
        "\n".join(
            [
                "# Consent Flow",
                "",
                "Stage 2.4 connects legal document versions with registration and user consent history.",
                "",
                "## Required documents",
                "",
                "Current required document types:",
                "",
                "- terms",
                "- privacy",
                "- personal_data",
                "",
                "## Registration rule",
                "",
                "A new user must submit accepted legal document versions during registration.",
                "",
                "Expected registration payload fragment:",
                "",
                "{",
                '  "accepted_legal_documents": [',
                '    {"document_type": "terms", "document_version": "1.0", "accepted": true},',
                '    {"document_type": "privacy", "document_version": "1.0", "accepted": true},',
                '    {"document_type": "personal_data", "document_version": "1.0", "accepted": true}',
                "  ]",
                "}",
                "",
                "## Backend behavior",
                "",
                "1. Backend ensures default active legal documents exist.",
                "2. Backend validates submitted document types and versions.",
                "3. Backend creates user.",
                "4. Backend records rows in user_consents.",
                "5. Backend writes audit event legal.consents_accepted.",
                "",
                "## Endpoints",
                "",
                "- GET /api/v1/legal/documents",
                "- GET /api/v1/legal/documents/current",
                "- GET /api/v1/legal/documents/{document_type}/current",
                "- GET /api/v1/consents/me",
                "- POST /api/v1/consents/accept-current",
                "",
            ]
        ),
    )

    write_text(
        "docs/privacy/legal-document-versions.md",
        "\n".join(
            [
                "# Legal Document Versions",
                "",
                "Legal documents are stored in legal_documents.",
                "",
                "## Versioning rule",
                "",
                "Each legal document has:",
                "",
                "- document_type",
                "- version",
                "- title",
                "- content",
                "- is_active",
                "- published_at",
                "",
                "## Required active documents",
                "",
                "The application currently requires:",
                "",
                "- terms",
                "- privacy",
                "- personal_data",
                "",
                "## Production warning",
                "",
                "Default legal document content is placeholder text.",
                "",
                "Before production release, replace placeholder content with final legal text.",
                "",
            ]
        ),
    )