$ErrorActionPreference = "Stop"

$Root = "D:\DevProject\PythonProject\VATranscribeWeb"

if (-not (Test-Path $Root)) {
    throw "Project root not found: $Root"
}

Set-Location $Root

function Write-TextFile {
    param(
        [string]$Path,
        [string[]]$Lines
    )

    $Parent = Split-Path $Path -Parent

    if ($Parent -and -not (Test-Path $Parent)) {
        New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    }

    Set-Content -Encoding UTF8 -Path $Path -Value $Lines
}

Write-Host "Stage 2.5: PrivacyRequest ORM + router + audit..."

# ============================================================
# 1. Patch models.py
# ============================================================

$ModelsPath = "apps\api\app\models.py"

if (-not (Test-Path $ModelsPath)) {
    throw "File not found: $ModelsPath"
}

$ModelsText = Get-Content -Raw -Encoding UTF8 $ModelsPath
$ModelsText = $ModelsText -replace "`r`n", "`n"

if ($ModelsText -notmatch "class PrivacyRequest\(Base\):") {
    $PrivacyModel = @'

class PrivacyRequest(Base):
    __tablename__ = "privacy_requests"

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
    request_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )
    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
    )

'@

    $Marker = "`nclass AuditLog(Base):"

    if ($ModelsText.Contains($Marker)) {
        $ModelsText = $ModelsText.Replace($Marker, "$PrivacyModel`nclass AuditLog(Base):")
    }
    else {
        $Marker = "`nclass LegalDocument(Base):"

        if (-not $ModelsText.Contains($Marker)) {
            throw "Could not find insertion point for PrivacyRequest model"
        }

        $ModelsText = $ModelsText.Replace($Marker, "$PrivacyModel`nclass LegalDocument(Base):")
    }

    Set-Content -Encoding UTF8 -Path $ModelsPath -Value $ModelsText
}

# ============================================================
# 2. Patch schemas.py
# ============================================================

$SchemasPath = "apps\api\app\schemas.py"

if (-not (Test-Path $SchemasPath)) {
    throw "File not found: $SchemasPath"
}

$SchemasText = Get-Content -Raw -Encoding UTF8 $SchemasPath
$SchemasText = $SchemasText -replace "`r`n", "`n"

if ($SchemasText -notmatch "class PrivacyRequestCreate\(BaseModel\):") {
    $PrivacySchemas = @'

class PrivacyRequestCreate(BaseModel):
    request_type: str = Field(pattern="^(export|delete_account|delete_files|revoke_consent)$")
    comment: str | None = Field(default=None, max_length=2000)


class PrivacyRequestRead(BaseModel):
    id: str
    user_id: str
    request_type: str
    status: str
    comment: str | None = None
    created_at: datetime | None = None
    processed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PrivacyOverviewResponse(BaseModel):
    status: str = "ok"
    requests: list[PrivacyRequestRead] = Field(default_factory=list)

'@

    $Marker = "class RegisterRequest(BaseModel):"

    if (-not $SchemasText.Contains($Marker)) {
        throw "Could not find RegisterRequest insertion point in schemas.py"
    }

    $SchemasText = $SchemasText.Replace($Marker, "$PrivacySchemas`nclass RegisterRequest(BaseModel):")

    Set-Content -Encoding UTF8 -Path $SchemasPath -Value $SchemasText
}

# ============================================================
# 3. Replace privacy_request_service.py
# ============================================================

Write-TextFile "apps\api\app\services\privacy_request_service.py" @(
    "from __future__ import annotations",
    "",
    "from fastapi import HTTPException, status",
    "from sqlalchemy import select",
    "from sqlalchemy.orm import Session",
    "",
    "from apps.api.app.models import PrivacyRequest, User",
    "",
    "",
    "ALLOWED_PRIVACY_REQUEST_TYPES: set[str] = {",
    "    'export',",
    "    'delete_account',",
    "    'delete_files',",
    "    'revoke_consent',",
    "}",
    "",
    "",
    "def ensure_valid_privacy_request_type(request_type: str) -> None:",
    "    if request_type not in ALLOWED_PRIVACY_REQUEST_TYPES:",
    "        raise HTTPException(",
    "            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,",
    "            detail='Unsupported privacy request type',",
    "        )",
    "",
    "",
    "def create_user_privacy_request(",
    "    db: Session,",
    "    user: User,",
    "    request_type: str,",
    "    comment: str | None = None,",
    ") -> PrivacyRequest:",
    "    ensure_valid_privacy_request_type(request_type)",
    "",
    "    row = PrivacyRequest(",
    "        user_id=user.id,",
    "        request_type=request_type,",
    "        status='pending',",
    "        comment=comment,",
    "    )",
    "",
    "    db.add(row)",
    "    db.flush()",
    "",
    "    return row",
    "",
    "",
    "def list_user_privacy_requests(",
    "    db: Session,",
    "    user: User,",
    ") -> list[PrivacyRequest]:",
    "    return list(",
    "        db.scalars(",
    "            select(PrivacyRequest)",
    "            .where(PrivacyRequest.user_id == user.id)",
    "            .order_by(PrivacyRequest.created_at.desc())",
    "        )",
    "    )",
    "",
    "",
    "class PrivacyRequestService:",
    "    allowed_request_types = ALLOWED_PRIVACY_REQUEST_TYPES",
    "",
    "    def validate_request_type(self, request_type: str) -> None:",
    "        if request_type not in self.allowed_request_types:",
    "            raise ValueError('Unsupported privacy request type')",
    "",
    "",
    "privacy_request_service = PrivacyRequestService()"
)

# ============================================================
# 4. Replace routers/privacy.py
# ============================================================

Write-TextFile "apps\api\app\routers\privacy.py" @(
    "from __future__ import annotations",
    "",
    "from fastapi import APIRouter, Depends, Request, status",
    "from sqlalchemy.orm import Session",
    "",
    "from apps.api.app.database import get_db",
    "from apps.api.app.dependencies import get_current_user",
    "from apps.api.app.models import User",
    "from apps.api.app.schemas import (",
    "    PrivacyOverviewResponse,",
    "    PrivacyRequestCreate,",
    "    PrivacyRequestRead,",
    ")",
    "from apps.api.app.services.audit_service import record_audit_event",
    "from apps.api.app.services.privacy_request_service import (",
    "    create_user_privacy_request,",
    "    list_user_privacy_requests,",
    ")",
    "",
    "",
    "router = APIRouter(prefix='/privacy', tags=['privacy'])",
    "",
    "",
    "@router.get('/me', response_model=PrivacyOverviewResponse)",
    "def get_my_privacy_overview(",
    "    db: Session = Depends(get_db),",
    "    current_user: User = Depends(get_current_user),",
    ") -> PrivacyOverviewResponse:",
    "    rows = list_user_privacy_requests(db, current_user)",
    "    return PrivacyOverviewResponse(status='ok', requests=rows)",
    "",
    "",
    "@router.post(",
    "    '/requests',",
    "    response_model=PrivacyRequestRead,",
    "    status_code=status.HTTP_201_CREATED,",
    ")",
    "def create_privacy_request(",
    "    payload: PrivacyRequestCreate,",
    "    request: Request,",
    "    db: Session = Depends(get_db),",
    "    current_user: User = Depends(get_current_user),",
    ") -> PrivacyRequestRead:",
    "    row = create_user_privacy_request(",
    "        db=db,",
    "        user=current_user,",
    "        request_type=payload.request_type,",
    "        comment=payload.comment,",
    "    )",
    "",
    "    record_audit_event(",
    "        db=db,",
    "        request=request,",
    "        action='privacy.request_created',",
    "        actor_user_id=str(current_user.id),",
    "        entity_type='PrivacyRequest',",
    "        entity_id=str(row.id),",
    "        meta={",
    "            'request_type': row.request_type,",
    "            'status': row.status,",
    "        },",
    "    )",
    "",
    "    db.commit()",
    "    db.refresh(row)",
    "",
    "    return row"
)

# ============================================================
# 5. Replace tests/privacy/test_privacy_requests.py
# ============================================================

Write-TextFile "tests\privacy\test_privacy_requests.py" @(
    "from pathlib import Path",
    "",
    "import pytest",
    "",
    "from apps.api.app.services.privacy_request_service import privacy_request_service",
    "",
    "",
    "ROOT = Path(__file__).resolve().parents[2]",
    "",
    "",
    "def read(path: str) -> str:",
    "    return (ROOT / path).read_text(encoding='utf-8')",
    "",
    "",
    "def test_validate_privacy_request_type_accepts_export():",
    "    privacy_request_service.validate_request_type('export')",
    "",
    "",
    "def test_validate_privacy_request_type_rejects_unknown():",
    "    with pytest.raises(ValueError):",
    "        privacy_request_service.validate_request_type('unknown')",
    "",
    "",
    "def test_privacy_request_model_exists():",
    "    text = read('apps/api/app/models.py')",
    "    assert 'class PrivacyRequest(Base):' in text",
    "    assert '__tablename__ = `"privacy_requests`"' in text",
    "    assert 'request_type' in text",
    "    assert 'processed_at' in text",
    "",
    "",
    "def test_privacy_request_schemas_exist():",
    "    text = read('apps/api/app/schemas.py')",
    "    assert 'class PrivacyRequestCreate(BaseModel):' in text",
    "    assert 'class PrivacyRequestRead(BaseModel):' in text",
    "    assert 'class PrivacyOverviewResponse(BaseModel):' in text",
    "",
    "",
    "def test_privacy_router_requires_current_user_and_writes_audit():",
    "    text = read('apps/api/app/routers/privacy.py')",
    "    assert 'Depends(get_current_user)' in text",
    "    assert 'create_user_privacy_request' in text",
    "    assert 'list_user_privacy_requests' in text",
    "    assert 'privacy.request_created' in text",
    "    assert 'record_audit_event' in text"
)

# ============================================================
# 6. Replace docs/privacy/privacy-requests.md
# ============================================================

Write-TextFile "docs\privacy\privacy-requests.md" @(
    "# Privacy Requests",
    "",
    "Stage 2.5 implements real privacy request persistence.",
    "",
    "## Supported request types",
    "",
    "- export",
    "- delete_account",
    "- delete_files",
    "- revoke_consent",
    "",
    "## Endpoints",
    "",
    "- GET /api/v1/privacy/me",
    "- POST /api/v1/privacy/requests",
    "",
    "## Request lifecycle",
    "",
    "New requests are created with status `pending`.",
    "",
    "Future admin workflow should process requests and set:",
    "",
    "- status",
    "- processed_at",
    "",
    "## Audit",
    "",
    "Creating a privacy request writes audit event:",
    "",
    "- privacy.request_created",
    "",
    "## Security",
    "",
    "Privacy requests are scoped to the authenticated user through `current_user.id`.",
    "Users can see only their own privacy request history."
)

Write-Host "Stage 2.5 privacy requests patch completed."
Write-Host ""
Write-Host "Next:"
Write-Host "docker compose build api"
Write-Host "docker compose up -d api"
Write-Host "docker compose exec api python -m pytest tests/security tests/privacy"
