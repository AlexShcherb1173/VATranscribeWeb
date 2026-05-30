$ErrorActionPreference = "Stop"

$Root = "D:\DevProject\PythonProject\VATranscribeWeb"

if (-not (Test-Path $Root)) {
    throw "Project root not found: $Root"
}

Set-Location $Root

Write-Host "Stage 2: Security and Privacy Foundation..."

$Dirs = @(
    "apps/api/app/security",
    "apps/api/app/services",
    "apps/api/app/schemas",
    "apps/api/app/routers",
    "alembic/versions",
    "tests/security",
    "tests/privacy",
    "docs/security",
    "docs/privacy"
)

foreach ($Dir in $Dirs) {
    New-Item -ItemType Directory -Force -Path $Dir | Out-Null
    $Gitkeep = Join-Path $Dir ".gitkeep"
    if (-not (Test-Path $Gitkeep)) {
        New-Item -ItemType File -Force -Path $Gitkeep | Out-Null
    }
}

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

# ============================================================
# Security helpers
# ============================================================

Write-TextFile "apps/api/app/security/password_policy.py" @(
    "from __future__ import annotations",
    "",
    "",
    "class PasswordPolicyError(ValueError):",
    "    pass",
    "",
    "",
    "def validate_password_strength(password: str) -> None:",
    "    if len(password) < 8:",
    "        raise PasswordPolicyError('Password must contain at least 8 characters')",
    "",
    "    if password.lower() == password:",
    "        raise PasswordPolicyError('Password must contain at least one uppercase letter')",
    "",
    "    if password.upper() == password:",
    "        raise PasswordPolicyError('Password must contain at least one lowercase letter')",
    "",
    "    if not any(ch.isdigit() for ch in password):",
    "        raise PasswordPolicyError('Password must contain at least one digit')",
    "",
    "",
    "def is_password_acceptable(password: str) -> bool:",
    "    try:",
    "        validate_password_strength(password)",
    "    except PasswordPolicyError:",
    "        return False",
    "    return True"
)

Write-TextFile "apps/api/app/security/ownership.py" @(
    "from __future__ import annotations",
    "",
    "from fastapi import HTTPException, status",
    "",
    "",
    "def assert_owner(resource_user_id: int | str, current_user_id: int | str) -> None:",
    "    if str(resource_user_id) != str(current_user_id):",
    "        raise HTTPException(",
    "            status_code=status.HTTP_404_NOT_FOUND,",
    "            detail='Resource not found',",
    "        )",
    "",
    "",
    "def is_owner(resource_user_id: int | str, current_user_id: int | str) -> bool:",
    "    return str(resource_user_id) == str(current_user_id)"
)

Write-TextFile "apps/api/app/security/rate_limits.py" @(
    "from __future__ import annotations",
    "",
    "import time",
    "from collections import defaultdict, deque",
    "",
    "from fastapi import HTTPException, status",
    "",
    "",
    "class InMemoryRateLimiter:",
    "    def __init__(self) -> None:",
    "        self._events: dict[str, deque[float]] = defaultdict(deque)",
    "",
    "    def check(self, key: str, limit: int, window_seconds: int) -> None:",
    "        now = time.time()",
    "        events = self._events[key]",
    "",
    "        while events and events[0] <= now - window_seconds:",
    "            events.popleft()",
    "",
    "        if len(events) >= limit:",
    "            raise HTTPException(",
    "                status_code=status.HTTP_429_TOO_MANY_REQUESTS,",
    "                detail='Too many requests',",
    "            )",
    "",
    "        events.append(now)",
    "",
    "",
    "rate_limiter = InMemoryRateLimiter()"
)

Write-TextFile "apps/api/app/security/token_rotation.py" @(
    "from __future__ import annotations",
    "",
    "import hashlib",
    "import secrets",
    "",
    "",
    "def generate_refresh_token() -> str:",
    "    return secrets.token_urlsafe(64)",
    "",
    "",
    "def hash_refresh_token(token: str) -> str:",
    "    return hashlib.sha256(token.encode('utf-8')).hexdigest()",
    "",
    "",
    "def verify_refresh_token_hash(token: str, token_hash: str) -> bool:",
    "    return hash_refresh_token(token) == token_hash"
)

Write-TextFile "apps/api/app/security/privacy.py" @(
    "from __future__ import annotations",
    "",
    "import hashlib",
    "",
    "",
    "def hash_ip_address(ip_address: str | None) -> str | None:",
    "    if not ip_address:",
    "        return None",
    "    return hashlib.sha256(ip_address.encode('utf-8')).hexdigest()",
    "",
    "",
    "def mask_email(email: str) -> str:",
    "    if '@' not in email:",
    "        return email",
    "    name, domain = email.split('@', 1)",
    "    if len(name) <= 2:",
    "        masked = '*' * len(name)",
    "    else:",
    "        masked = name[0] + '*' * (len(name) - 2) + name[-1]",
    "    return masked + '@' + domain"
)

# ============================================================
# Schemas
# ============================================================

Write-TextFile "apps/api/app/schemas/consent.py" @(
    "from __future__ import annotations",
    "",
    "from datetime import datetime",
    "from pydantic import BaseModel, Field",
    "",
    "",
    "class ConsentCreate(BaseModel):",
    "    document_type: str = Field(min_length=2, max_length=100)",
    "    document_version: str = Field(min_length=1, max_length=50)",
    "    accepted: bool = True",
    "",
    "",
    "class ConsentRead(BaseModel):",
    "    id: int",
    "    user_id: int",
    "    document_type: str",
    "    document_version: str",
    "    accepted: bool",
    "    created_at: datetime",
    "",
    "    model_config = {'from_attributes': True}"
)

Write-TextFile "apps/api/app/schemas/legal.py" @(
    "from __future__ import annotations",
    "",
    "from datetime import datetime",
    "from pydantic import BaseModel, Field",
    "",
    "",
    "class LegalDocumentRead(BaseModel):",
    "    id: int",
    "    document_type: str",
    "    version: str",
    "    title: str",
    "    is_active: bool",
    "    published_at: datetime | None = None",
    "",
    "    model_config = {'from_attributes': True}",
    "",
    "",
    "class LegalDocumentCreate(BaseModel):",
    "    document_type: str = Field(min_length=2, max_length=100)",
    "    version: str = Field(min_length=1, max_length=50)",
    "    title: str = Field(min_length=2, max_length=255)",
    "    content: str = Field(min_length=1)"
)

Write-TextFile "apps/api/app/schemas/privacy.py" @(
    "from __future__ import annotations",
    "",
    "from datetime import datetime",
    "from pydantic import BaseModel, Field",
    "",
    "",
    "class PrivacyRequestCreate(BaseModel):",
    "    request_type: str = Field(pattern='^(export|delete_account|delete_files|revoke_consent)$')",
    "    comment: str | None = None",
    "",
    "",
    "class PrivacyRequestRead(BaseModel):",
    "    id: int",
    "    user_id: int",
    "    request_type: str",
    "    status: str",
    "    created_at: datetime",
    "    processed_at: datetime | None = None",
    "",
    "    model_config = {'from_attributes': True}"
)

Write-TextFile "apps/api/app/schemas/audit.py" @(
    "from __future__ import annotations",
    "",
    "from datetime import datetime",
    "from pydantic import BaseModel",
    "",
    "",
    "class AuditLogRead(BaseModel):",
    "    id: int",
    "    actor_user_id: int | None = None",
    "    action: str",
    "    entity_type: str | None = None",
    "    entity_id: str | None = None",
    "    created_at: datetime",
    "",
    "    model_config = {'from_attributes': True}"
)

Write-TextFile "apps/api/app/schemas/security.py" @(
    "from __future__ import annotations",
    "",
    "from datetime import datetime",
    "from pydantic import BaseModel",
    "",
    "",
    "class SecurityEventRead(BaseModel):",
    "    id: int",
    "    user_id: int | None = None",
    "    event_type: str",
    "    severity: str",
    "    created_at: datetime",
    "",
    "    model_config = {'from_attributes': True}"
)

# ============================================================
# Services
# ============================================================

Write-TextFile "apps/api/app/services/audit_service.py" @(
    "from __future__ import annotations",
    "",
    "from typing import Any",
    "",
    "",
    "class AuditService:",
    "    def build_event(",
    "        self,",
    "        action: str,",
    "        actor_user_id: int | None = None,",
    "        entity_type: str | None = None,",
    "        entity_id: str | None = None,",
    "        meta: dict[str, Any] | None = None,",
    "    ) -> dict[str, Any]:",
    "        return {",
    "            'action': action,",
    "            'actor_user_id': actor_user_id,",
    "            'entity_type': entity_type,",
    "            'entity_id': entity_id,",
    "            'meta': meta or {},",
    "        }",
    "",
    "",
    "audit_service = AuditService()"
)

Write-TextFile "apps/api/app/services/consent_service.py" @(
    "from __future__ import annotations",
    "",
    "from typing import Any",
    "",
    "",
    "class ConsentService:",
    "    def build_consent_record(",
    "        self,",
    "        user_id: int,",
    "        document_type: str,",
    "        document_version: str,",
    "        accepted: bool = True,",
    "    ) -> dict[str, Any]:",
    "        return {",
    "            'user_id': user_id,",
    "            'document_type': document_type,",
    "            'document_version': document_version,",
    "            'accepted': accepted,",
    "        }",
    "",
    "",
    "consent_service = ConsentService()"
)

Write-TextFile "apps/api/app/services/legal_document_service.py" @(
    "from __future__ import annotations",
    "",
    "",
    "class LegalDocumentService:",
    "    def normalize_document_type(self, document_type: str) -> str:",
    "        return document_type.strip().lower().replace(' ', '_')",
    "",
    "",
    "legal_document_service = LegalDocumentService()"
)

Write-TextFile "apps/api/app/services/privacy_request_service.py" @(
    "from __future__ import annotations",
    "",
    "",
    "class PrivacyRequestService:",
    "    allowed_request_types = {'export', 'delete_account', 'delete_files', 'revoke_consent'}",
    "",
    "    def validate_request_type(self, request_type: str) -> None:",
    "        if request_type not in self.allowed_request_types:",
    "            raise ValueError('Unsupported privacy request type')",
    "",
    "",
    "privacy_request_service = PrivacyRequestService()"
)

Write-TextFile "apps/api/app/services/security_event_service.py" @(
    "from __future__ import annotations",
    "",
    "",
    "class SecurityEventService:",
    "    def normalize_severity(self, severity: str) -> str:",
    "        normalized = severity.strip().lower()",
    "        if normalized not in {'low', 'medium', 'high', 'critical'}:",
    "            return 'medium'",
    "        return normalized",
    "",
    "",
    "security_event_service = SecurityEventService()"
)

# ============================================================
# Routers
# ============================================================

Write-TextFile "apps/api/app/routers/consents.py" @(
    "from __future__ import annotations",
    "",
    "from fastapi import APIRouter",
    "",
    "from apps.api.app.schemas.consent import ConsentCreate",
    "from apps.api.app.services.consent_service import consent_service",
    "",
    "router = APIRouter(prefix='/consents', tags=['consents'])",
    "",
    "",
    "@router.get('/me')",
    "def list_my_consents() -> dict[str, list[dict]]:",
    "    return {'items': []}",
    "",
    "",
    "@router.post('')",
    "def create_consent(payload: ConsentCreate) -> dict:",
    "    record = consent_service.build_consent_record(",
    "        user_id=0,",
    "        document_type=payload.document_type,",
    "        document_version=payload.document_version,",
    "        accepted=payload.accepted,",
    "    )",
    "    return {'status': 'accepted', 'consent': record}"
)

Write-TextFile "apps/api/app/routers/legal.py" @(
    "from __future__ import annotations",
    "",
    "from fastapi import APIRouter",
    "",
    "router = APIRouter(prefix='/legal', tags=['legal'])",
    "",
    "",
    "@router.get('/documents')",
    "def list_legal_documents() -> dict[str, list[dict]]:",
    "    return {'items': []}",
    "",
    "",
    "@router.get('/documents/{document_type}/current')",
    "def get_current_legal_document(document_type: str) -> dict:",
    "    return {'document_type': document_type, 'status': 'not_configured'}"
)

Write-TextFile "apps/api/app/routers/privacy.py" @(
    "from __future__ import annotations",
    "",
    "from fastapi import APIRouter",
    "",
    "from apps.api.app.schemas.privacy import PrivacyRequestCreate",
    "from apps.api.app.services.privacy_request_service import privacy_request_service",
    "",
    "router = APIRouter(prefix='/privacy', tags=['privacy'])",
    "",
    "",
    "@router.get('/me')",
    "def get_my_privacy_overview() -> dict:",
    "    return {'status': 'ok', 'requests': []}",
    "",
    "",
    "@router.post('/requests')",
    "def create_privacy_request(payload: PrivacyRequestCreate) -> dict:",
    "    privacy_request_service.validate_request_type(payload.request_type)",
    "    return {'status': 'created', 'request_type': payload.request_type}"
)

Write-TextFile "apps/api/app/routers/security.py" @(
    "from __future__ import annotations",
    "",
    "from fastapi import APIRouter, Request",
    "",
    "from apps.api.app.security.rate_limits import rate_limiter",
    "",
    "router = APIRouter(prefix='/security', tags=['security'])",
    "",
    "",
    "@router.get('/ping-rate-limit')",
    "def ping_rate_limit(request: Request) -> dict[str, str]:",
    "    client = request.client.host if request.client else 'unknown'",
    "    rate_limiter.check(key='security_ping:' + client, limit=10, window_seconds=60)",
    "    return {'status': 'ok'}"
)

# ============================================================
# Alembic migration
# ============================================================

Write-TextFile "alembic/versions/20260529_0001_security_privacy_foundation.py" @(
    '"""security privacy foundation"""',
    "",
    "from __future__ import annotations",
    "",
    "from alembic import op",
    "import sqlalchemy as sa",
    "",
    "",
    "revision = '20260529_0001_security_privacy_foundation'",
    "down_revision = None",
    "branch_labels = None",
    "depends_on = None",
    "",
    "",
    "def upgrade() -> None:",
    "    op.create_table(",
    "        'legal_documents',",
    "        sa.Column('id', sa.Integer(), primary_key=True),",
    "        sa.Column('document_type', sa.String(length=100), nullable=False),",
    "        sa.Column('version', sa.String(length=50), nullable=False),",
    "        sa.Column('title', sa.String(length=255), nullable=False),",
    "        sa.Column('content', sa.Text(), nullable=False),",
    "        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('false')),",
    "        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),",
    "        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),",
    "    )",
    "    op.create_index('ix_legal_documents_type_version', 'legal_documents', ['document_type', 'version'], unique=True)",
    "",
    "    op.create_table(",
    "        'user_consents',",
    "        sa.Column('id', sa.Integer(), primary_key=True),",
    "        sa.Column('user_id', sa.Integer(), nullable=False),",
    "        sa.Column('document_type', sa.String(length=100), nullable=False),",
    "        sa.Column('document_version', sa.String(length=50), nullable=False),",
    "        sa.Column('accepted', sa.Boolean(), nullable=False, server_default=sa.text('true')),",
    "        sa.Column('ip_hash', sa.String(length=128), nullable=True),",
    "        sa.Column('user_agent_hash', sa.String(length=128), nullable=True),",
    "        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),",
    "    )",
    "    op.create_index('ix_user_consents_user_id', 'user_consents', ['user_id'])",
    "",
    "    op.create_table(",
    "        'privacy_requests',",
    "        sa.Column('id', sa.Integer(), primary_key=True),",
    "        sa.Column('user_id', sa.Integer(), nullable=False),",
    "        sa.Column('request_type', sa.String(length=50), nullable=False),",
    "        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),",
    "        sa.Column('comment', sa.Text(), nullable=True),",
    "        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),",
    "        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),",
    "    )",
    "    op.create_index('ix_privacy_requests_user_id', 'privacy_requests', ['user_id'])",
    "",
    "    op.create_table(",
    "        'audit_logs',",
    "        sa.Column('id', sa.Integer(), primary_key=True),",
    "        sa.Column('actor_user_id', sa.Integer(), nullable=True),",
    "        sa.Column('action', sa.String(length=150), nullable=False),",
    "        sa.Column('entity_type', sa.String(length=100), nullable=True),",
    "        sa.Column('entity_id', sa.String(length=100), nullable=True),",
    "        sa.Column('meta_json', sa.JSON(), nullable=True),",
    "        sa.Column('ip_hash', sa.String(length=128), nullable=True),",
    "        sa.Column('user_agent_hash', sa.String(length=128), nullable=True),",
    "        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),",
    "    )",
    "    op.create_index('ix_audit_logs_actor_user_id', 'audit_logs', ['actor_user_id'])",
    "",
    "    op.create_table(",
    "        'security_events',",
    "        sa.Column('id', sa.Integer(), primary_key=True),",
    "        sa.Column('user_id', sa.Integer(), nullable=True),",
    "        sa.Column('event_type', sa.String(length=150), nullable=False),",
    "        sa.Column('severity', sa.String(length=20), nullable=False, server_default='medium'),",
    "        sa.Column('meta_json', sa.JSON(), nullable=True),",
    "        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),",
    "    )",
    "    op.create_index('ix_security_events_user_id', 'security_events', ['user_id'])",
    "",
    "    op.create_table(",
    "        'refresh_tokens',",
    "        sa.Column('id', sa.Integer(), primary_key=True),",
    "        sa.Column('user_id', sa.Integer(), nullable=False),",
    "        sa.Column('token_hash', sa.String(length=128), nullable=False, unique=True),",
    "        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),",
    "        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),",
    "        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),",
    "        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),",
    "    )",
    "    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])",
    "",
    "",
    "def downgrade() -> None:",
    "    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')",
    "    op.drop_table('refresh_tokens')",
    "    op.drop_index('ix_security_events_user_id', table_name='security_events')",
    "    op.drop_table('security_events')",
    "    op.drop_index('ix_audit_logs_actor_user_id', table_name='audit_logs')",
    "    op.drop_table('audit_logs')",
    "    op.drop_index('ix_privacy_requests_user_id', table_name='privacy_requests')",
    "    op.drop_table('privacy_requests')",
    "    op.drop_index('ix_user_consents_user_id', table_name='user_consents')",
    "    op.drop_table('user_consents')",
    "    op.drop_index('ix_legal_documents_type_version', table_name='legal_documents')",
    "    op.drop_table('legal_documents')"
)

# ============================================================
# Tests
# ============================================================

Write-TextFile "tests/security/test_password_policy.py" @(
    "import pytest",
    "",
    "from apps.api.app.security.password_policy import PasswordPolicyError, validate_password_strength",
    "",
    "",
    "def test_password_policy_accepts_strong_password():",
    "    validate_password_strength('StrongPass123')",
    "",
    "",
    "def test_password_policy_rejects_short_password():",
    "    with pytest.raises(PasswordPolicyError):",
    "        validate_password_strength('A1b')"
)

Write-TextFile "tests/security/test_ownership.py" @(
    "import pytest",
    "from fastapi import HTTPException",
    "",
    "from apps.api.app.security.ownership import assert_owner, is_owner",
    "",
    "",
    "def test_is_owner_true():",
    "    assert is_owner(1, 1) is True",
    "",
    "",
    "def test_assert_owner_raises_for_non_owner():",
    "    with pytest.raises(HTTPException):",
    "        assert_owner(1, 2)"
)

Write-TextFile "tests/security/test_rate_limits.py" @(
    "import pytest",
    "from fastapi import HTTPException",
    "",
    "from apps.api.app.security.rate_limits import InMemoryRateLimiter",
    "",
    "",
    "def test_rate_limiter_blocks_after_limit():",
    "    limiter = InMemoryRateLimiter()",
    "    limiter.check('k', limit=1, window_seconds=60)",
    "    with pytest.raises(HTTPException):",
    "        limiter.check('k', limit=1, window_seconds=60)"
)

Write-TextFile "tests/privacy/test_consents.py" @(
    "from apps.api.app.services.consent_service import consent_service",
    "",
    "",
    "def test_build_consent_record():",
    "    record = consent_service.build_consent_record(",
    "        user_id=1,",
    "        document_type='privacy',",
    "        document_version='1.0',",
    "    )",
    "    assert record['user_id'] == 1",
    "    assert record['accepted'] is True"
)

Write-TextFile "tests/privacy/test_privacy_requests.py" @(
    "import pytest",
    "",
    "from apps.api.app.services.privacy_request_service import privacy_request_service",
    "",
    "",
    "def test_validate_privacy_request_type_accepts_export():",
    "    privacy_request_service.validate_request_type('export')",
    "",
    "",
    "def test_validate_privacy_request_type_rejects_unknown():",
    "    with pytest.raises(ValueError):",
    "        privacy_request_service.validate_request_type('unknown')"
)

Write-TextFile "tests/privacy/test_legal_documents.py" @(
    "from apps.api.app.services.legal_document_service import legal_document_service",
    "",
    "",
    "def test_normalize_document_type():",
    "    assert legal_document_service.normalize_document_type('Privacy Policy') == 'privacy_policy'"
)

# ============================================================
# Docs
# ============================================================

Write-TextFile "docs/security/auth-hardening.md" @(
    "# Auth Hardening",
    "",
    "Stage 2 target:",
    "- enforce password policy",
    "- store only password hashes",
    "- add refresh token rotation",
    "- revoke refresh tokens on logout",
    "- revoke refresh tokens on password change",
    "- add login rate limits",
    "- add audit events for auth actions"
)

Write-TextFile "docs/security/refresh-token-rotation.md" @(
    "# Refresh Token Rotation",
    "",
    "Refresh tokens must be stored as hashes.",
    "",
    "Flow:",
    "1. User logs in.",
    "2. API issues access token and refresh token.",
    "3. Refresh token hash is stored in DB.",
    "4. On refresh, old token is revoked.",
    "5. New refresh token is issued and stored.",
    "6. Reuse of revoked token is treated as security event."
)

Write-TextFile "docs/security/file-ownership.md" @(
    "# File Ownership",
    "",
    "Every file/media/job/transcript/export must be scoped by user_id.",
    "",
    "Rule:",
    "Do not fetch by id only. Always fetch by id plus current_user.id."
)

Write-TextFile "docs/security/rate-limits.md" @(
    "# Rate Limits",
    "",
    "Initial rate limit targets:",
    "- login",
    "- register",
    "- password reset",
    "- upload",
    "- URL analysis",
    "- download job creation",
    "- payment checkout creation",
    "- webhook endpoints by provider signature validation"
)

Write-TextFile "docs/security/audit-logs.md" @(
    "# Audit Logs",
    "",
    "Audit logs should be used for important user/admin/security actions.",
    "",
    "Examples:",
    "- login_success",
    "- login_failed",
    "- password_changed",
    "- subscription_changed",
    "- payment_refunded",
    "- admin_user_updated",
    "- file_deleted",
    "- privacy_request_created"
)

Write-TextFile "docs/privacy/consent-flow.md" @(
    "# Consent Flow",
    "",
    "Users must accept current legal document versions.",
    "",
    "Tracked documents:",
    "- terms",
    "- privacy",
    "- offer",
    "- personal_data",
    "- cookies",
    "- license",
    "- refund_policy"
)

Write-TextFile "docs/privacy/privacy-requests.md" @(
    "# Privacy Requests",
    "",
    "Supported request types:",
    "- export",
    "- delete_account",
    "- delete_files",
    "- revoke_consent",
    "",
    "Requests start as pending and must be processed by backend/admin flow."
)

Write-TextFile "docs/privacy/legal-document-versions.md" @(
    "# Legal Document Versions",
    "",
    "Legal documents must be versioned.",
    "",
    "Only one version per document_type should be active.",
    "",
    "User consent must reference document_type and document_version."
)

Write-Host "Stage 2 security and privacy foundation created."
Write-Host ""
Write-Host "Next commands:"
Write-Host "git status"
Write-Host "pytest tests/security tests/privacy"
Write-Host "docker compose exec api alembic heads"
Write-Host "docker compose exec api alembic upgrade head"
Write-Host "git add ."
Write-Host 'git commit -m "feat: add security and privacy foundation"'