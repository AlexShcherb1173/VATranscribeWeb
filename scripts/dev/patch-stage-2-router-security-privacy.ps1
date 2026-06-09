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

Write-Host "Patching Stage 2 routers and migration..."

# ============================================================
# routers/__init__.py
# ============================================================

Write-TextFile "apps/api/app/routers/__init__.py" @(
    "from __future__ import annotations",
    "",
    "from fastapi import APIRouter",
    "",
    "from apps.api.app.routers.auth import router as auth_router",
    "from apps.api.app.routers.billing import router as billing_router",
    "from apps.api.app.routers.downloads import router as downloads_router",
    "from apps.api.app.routers.export_artifacts import router as export_artifacts_router",
    "from apps.api.app.routers.health import router as health_router",
    "from apps.api.app.routers.jobs import router as jobs_router",
    "from apps.api.app.routers.media_assets import router as media_assets_router",
    "from apps.api.app.routers.profile import router as profile_router",
    "from apps.api.app.routers.quota import router as quota_router",
    "from apps.api.app.routers.settings import router as settings_router",
    "from apps.api.app.routers.transcriptions import router as transcriptions_router",
    "from apps.api.app.routers.transcripts import router as transcripts_router",
    "from apps.api.app.routers.uploads import router as uploads_router",
    "",
    "# Stage 2 security/privacy foundation routers",
    "from apps.api.app.routers.consents import router as consents_router",
    "from apps.api.app.routers.legal import router as legal_router",
    "from apps.api.app.routers.privacy import router as privacy_router",
    "from apps.api.app.routers.security import router as security_router",
    "",
    "",
    "router = APIRouter()",
    "",
    "# Core transferred routers",
    "router.include_router(health_router)",
    "router.include_router(auth_router)",
    "router.include_router(profile_router)",
    "router.include_router(quota_router)",
    "router.include_router(billing_router)",
    "router.include_router(jobs_router)",
    "router.include_router(downloads_router)",
    "router.include_router(uploads_router)",
    "router.include_router(media_assets_router)",
    "router.include_router(transcriptions_router)",
    "router.include_router(transcripts_router)",
    "router.include_router(export_artifacts_router)",
    "router.include_router(settings_router)",
    "",
    "# Stage 2 security/privacy foundation routers",
    "router.include_router(consents_router)",
    "router.include_router(legal_router)",
    "router.include_router(privacy_router)",
    "router.include_router(security_router)"
)

# ============================================================
# consents.py
# Inline schemas because current project uses apps/api/app/schemas.py file,
# not apps/api/app/schemas/ package.
# ============================================================

Write-TextFile "apps/api/app/routers/consents.py" @(
    "from __future__ import annotations",
    "",
    "from pydantic import BaseModel, Field",
    "from fastapi import APIRouter",
    "",
    "from apps.api.app.services.consent_service import consent_service",
    "",
    "",
    "router = APIRouter(prefix='/consents', tags=['consents'])",
    "",
    "",
    "class ConsentCreate(BaseModel):",
    "    document_type: str = Field(min_length=2, max_length=100)",
    "    document_version: str = Field(min_length=1, max_length=50)",
    "    accepted: bool = True",
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

# ============================================================
# legal.py
# ============================================================

Write-TextFile "apps/api/app/routers/legal.py" @(
    "from __future__ import annotations",
    "",
    "from fastapi import APIRouter",
    "",
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
    "    return {",
    "        'document_type': document_type,",
    "        'status': 'not_configured',",
    "    }"
)

# ============================================================
# privacy.py
# Inline schema because current project uses schemas.py file.
# ============================================================

Write-TextFile "apps/api/app/routers/privacy.py" @(
    "from __future__ import annotations",
    "",
    "from pydantic import BaseModel, Field",
    "from fastapi import APIRouter",
    "",
    "from apps.api.app.services.privacy_request_service import privacy_request_service",
    "",
    "",
    "router = APIRouter(prefix='/privacy', tags=['privacy'])",
    "",
    "",
    "class PrivacyRequestCreate(BaseModel):",
    "    request_type: str = Field(pattern='^(export|delete_account|delete_files|revoke_consent)$')",
    "    comment: str | None = None",
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
    "    return {",
    "        'status': 'created',",
    "        'request_type': payload.request_type,",
    "    }"
)

# ============================================================
# security.py
# ============================================================

Write-TextFile "apps/api/app/routers/security.py" @(
    "from __future__ import annotations",
    "",
    "from fastapi import APIRouter, Request",
    "",
    "from apps.api.app.security.rate_limits import rate_limiter",
    "",
    "",
    "router = APIRouter(prefix='/security', tags=['security'])",
    "",
    "",
    "@router.get('/ping-rate-limit')",
    "def ping_rate_limit(request: Request) -> dict[str, str]:",
    "    client = request.client.host if request.client else 'unknown'",
    "    rate_limiter.check(",
    "        key='security_ping:' + client,",
    "        limit=10,",
    "        window_seconds=60,",
    "    )",
    "    return {'status': 'ok'}"
)

# ============================================================
# main.py
# Ensure storage dirs are created before StaticFiles mount.
# ============================================================

Write-TextFile "apps/api/app/main.py" @(
    "from __future__ import annotations",
    "",
    "from contextlib import asynccontextmanager",
    "",
    "from fastapi import FastAPI",
    "from fastapi.middleware.cors import CORSMiddleware",
    "from fastapi.staticfiles import StaticFiles",
    "",
    "from apps.api.app.config import get_settings",
    "from apps.api.app.routers import router as api_router",
    "from apps.api.app.schemas import ApiInfoResponse",
    "",
    "settings = get_settings()",
    "",
    "",
    "def ensure_storage_dirs() -> None:",
    "    for path in settings.storage_dirs:",
    "        path.mkdir(parents=True, exist_ok=True)",
    "",
    "",
    "ensure_storage_dirs()",
    "",
    "",
    "@asynccontextmanager",
    "async def lifespan(_: FastAPI):",
    "    ensure_storage_dirs()",
    "    yield",
    "",
    "",
    "app = FastAPI(",
    "    title=settings.app_name,",
    "    debug=settings.debug,",
    "    lifespan=lifespan,",
    "    docs_url='/docs',",
    "    redoc_url='/redoc',",
    "    openapi_url='/openapi.json',",
    ")",
    "",
    "app.add_middleware(",
    "    CORSMiddleware,",
    "    allow_origins=settings.cors_origins_list,",
    "    allow_credentials=True,",
    "    allow_methods=['*'],",
    "    allow_headers=['*'],",
    ")",
    "",
    "app.include_router(api_router, prefix=settings.api_prefix)",
    "app.mount('/storage', StaticFiles(directory='storage'), name='storage')",
    "",
    "",
    "@app.get('/', response_model=ApiInfoResponse, tags=['meta'])",
    "def root() -> ApiInfoResponse:",
    "    return ApiInfoResponse(",
    "        app=settings.app_name,",
    "        env=settings.app_env,",
    "        version='0.1.0',",
    "        docs_url='/docs',",
    "        api_prefix=settings.api_prefix,",
    "        endpoints={",
    "            'health_live': f'{settings.api_prefix}/health/live',",
    "            'health_ready': f'{settings.api_prefix}/health/ready',",
    "            'auth_register': f'{settings.api_prefix}/auth/register',",
    "            'auth_login': f'{settings.api_prefix}/auth/login',",
    "            'auth_me': f'{settings.api_prefix}/auth/me',",
    "            'profile': f'{settings.api_prefix}/profile',",
    "            'quota': f'{settings.api_prefix}/quota/me',",
    "            'billing_overview': f'{settings.api_prefix}/billing/overview',",
    "            'billing_upgrade': f'{settings.api_prefix}/billing/upgrade',",
    "            'jobs_list': f'{settings.api_prefix}/jobs',",
    "            'jobs_get': f'{settings.api_prefix}/jobs/{{job_id}}',",
    "            'jobs_create': f'{settings.api_prefix}/jobs',",
    "            'jobs_logs': f'{settings.api_prefix}/jobs/{{job_id}}/logs',",
    "            'jobs_enqueue': f'{settings.api_prefix}/jobs/{{job_id}}/enqueue',",
    "            'jobs_retry': f'{settings.api_prefix}/jobs/{{job_id}}/retry',",
    "            'jobs_cancel': f'{settings.api_prefix}/jobs/{{job_id}}/cancel',",
    "            'downloads_analyze': f'{settings.api_prefix}/downloads/analyze',",
    "            'downloads_jobs': f'{settings.api_prefix}/downloads/jobs',",
    "            'uploads': f'{settings.api_prefix}/uploads',",
    "            'media_assets_list': f'{settings.api_prefix}/media-assets',",
    "            'media_asset_get': f'{settings.api_prefix}/media-assets/{{media_asset_id}}',",
    "            'media_asset_download': f'{settings.api_prefix}/media-assets/{{media_asset_id}}/download',",
    "            'media_asset_delete': f'{settings.api_prefix}/media-assets/{{media_asset_id}}',",
    "            'transcriptions_jobs': f'{settings.api_prefix}/transcriptions/jobs',",
    "            'transcripts_list': f'{settings.api_prefix}/transcripts',",
    "            'transcript_get': f'{settings.api_prefix}/transcripts/{{transcript_id}}',",
    "            'transcript_delete': f'{settings.api_prefix}/transcripts/{{transcript_id}}',",
    "            'export_artifact_get': f'{settings.api_prefix}/export-artifacts/{{artifact_id}}',",
    "            'export_artifact_download': f'{settings.api_prefix}/export-artifacts/{{artifact_id}}/download',",
    "            'export_artifact_delete': f'{settings.api_prefix}/export-artifacts/{{artifact_id}}',",
    "            'consents': f'{settings.api_prefix}/consents/me',",
    "            'legal_documents': f'{settings.api_prefix}/legal/documents',",
    "            'privacy': f'{settings.api_prefix}/privacy/me',",
    "            'security_ping': f'{settings.api_prefix}/security/ping-rate-limit',",
    "            'storage_static': '/storage/...',",
    "        },",
    "    )"
)

# ============================================================
# Alembic migration
# Current head in transferred chain is 20260524_0004_lyrics.
# Also user ids in this project are strings, not integers.
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
    "down_revision = '20260524_0004_lyrics'",
    "branch_labels = None",
    "depends_on = None",
    "",
    "",
    "def upgrade() -> None:",
    "    op.create_table(",
    "        'legal_documents',",
    "        sa.Column('id', sa.String(length=36), primary_key=True),",
    "        sa.Column('document_type', sa.String(length=100), nullable=False),",
    "        sa.Column('version', sa.String(length=50), nullable=False),",
    "        sa.Column('title', sa.String(length=255), nullable=False),",
    "        sa.Column('content', sa.Text(), nullable=False),",
    "        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('false')),",
    "        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),",
    "        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),",
    "        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),",
    "    )",
    "    op.create_index('ix_legal_documents_type_version', 'legal_documents', ['document_type', 'version'], unique=True)",
    "    op.create_index('ix_legal_documents_document_type', 'legal_documents', ['document_type'], unique=False)",
    "",
    "    op.create_table(",
    "        'user_consents',",
    "        sa.Column('id', sa.String(length=36), primary_key=True),",
    "        sa.Column('user_id', sa.String(length=36), nullable=False),",
    "        sa.Column('document_type', sa.String(length=100), nullable=False),",
    "        sa.Column('document_version', sa.String(length=50), nullable=False),",
    "        sa.Column('accepted', sa.Boolean(), nullable=False, server_default=sa.text('true')),",
    "        sa.Column('ip_hash', sa.String(length=128), nullable=True),",
    "        sa.Column('user_agent_hash', sa.String(length=128), nullable=True),",
    "        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),",
    "        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),",
    "    )",
    "    op.create_index('ix_user_consents_user_id', 'user_consents', ['user_id'], unique=False)",
    "    op.create_index('ix_user_consents_user_doc_version', 'user_consents', ['user_id', 'document_type', 'document_version'], unique=False)",
    "",
    "    op.create_table(",
    "        'privacy_requests',",
    "        sa.Column('id', sa.String(length=36), primary_key=True),",
    "        sa.Column('user_id', sa.String(length=36), nullable=False),",
    "        sa.Column('request_type', sa.String(length=50), nullable=False),",
    "        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),",
    "        sa.Column('comment', sa.Text(), nullable=True),",
    "        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),",
    "        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),",
    "        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),",
    "    )",
    "    op.create_index('ix_privacy_requests_user_id', 'privacy_requests', ['user_id'], unique=False)",
    "    op.create_index('ix_privacy_requests_status', 'privacy_requests', ['status'], unique=False)",
    "",
    "    op.create_table(",
    "        'audit_logs',",
    "        sa.Column('id', sa.String(length=36), primary_key=True),",
    "        sa.Column('actor_user_id', sa.String(length=36), nullable=True),",
    "        sa.Column('action', sa.String(length=150), nullable=False),",
    "        sa.Column('entity_type', sa.String(length=100), nullable=True),",
    "        sa.Column('entity_id', sa.String(length=100), nullable=True),",
    "        sa.Column('meta_json', sa.JSON(), nullable=True),",
    "        sa.Column('ip_hash', sa.String(length=128), nullable=True),",
    "        sa.Column('user_agent_hash', sa.String(length=128), nullable=True),",
    "        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),",
    "        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),",
    "    )",
    "    op.create_index('ix_audit_logs_actor_user_id', 'audit_logs', ['actor_user_id'], unique=False)",
    "    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'], unique=False)",
    "",
    "    op.create_table(",
    "        'security_events',",
    "        sa.Column('id', sa.String(length=36), primary_key=True),",
    "        sa.Column('user_id', sa.String(length=36), nullable=True),",
    "        sa.Column('event_type', sa.String(length=150), nullable=False),",
    "        sa.Column('severity', sa.String(length=20), nullable=False, server_default='medium'),",
    "        sa.Column('meta_json', sa.JSON(), nullable=True),",
    "        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),",
    "        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),",
    "    )",
    "    op.create_index('ix_security_events_user_id', 'security_events', ['user_id'], unique=False)",
    "    op.create_index('ix_security_events_event_type', 'security_events', ['event_type'], unique=False)",
    "",
    "    op.create_table(",
    "        'refresh_tokens',",
    "        sa.Column('id', sa.String(length=36), primary_key=True),",
    "        sa.Column('user_id', sa.String(length=36), nullable=False),",
    "        sa.Column('token_hash', sa.String(length=128), nullable=False, unique=True),",
    "        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),",
    "        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),",
    "        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),",
    "        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),",
    "        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),",
    "    )",
    "    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'], unique=False)",
    "",
    "",
    "def downgrade() -> None:",
    "    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')",
    "    op.drop_table('refresh_tokens')",
    "    op.drop_index('ix_security_events_event_type', table_name='security_events')",
    "    op.drop_index('ix_security_events_user_id', table_name='security_events')",
    "    op.drop_table('security_events')",
    "    op.drop_index('ix_audit_logs_action', table_name='audit_logs')",
    "    op.drop_index('ix_audit_logs_actor_user_id', table_name='audit_logs')",
    "    op.drop_table('audit_logs')",
    "    op.drop_index('ix_privacy_requests_status', table_name='privacy_requests')",
    "    op.drop_index('ix_privacy_requests_user_id', table_name='privacy_requests')",
    "    op.drop_table('privacy_requests')",
    "    op.drop_index('ix_user_consents_user_doc_version', table_name='user_consents')",
    "    op.drop_index('ix_user_consents_user_id', table_name='user_consents')",
    "    op.drop_table('user_consents')",
    "    op.drop_index('ix_legal_documents_document_type', table_name='legal_documents')",
    "    op.drop_index('ix_legal_documents_type_version', table_name='legal_documents')",
    "    op.drop_table('legal_documents')"
)

Write-Host "Stage 2 router/security/privacy patch completed."
Write-Host ""
Write-Host "Next:"
Write-Host "docker compose restart api"
Write-Host "docker compose logs api --tail=80"
Write-Host "curl http://localhost:8000/api/v1/legal/documents"
Write-Host "curl http://localhost:8000/api/v1/privacy/me"
Write-Host "curl http://localhost:8000/api/v1/consents/me"
Write-Host "curl http://localhost:8000/api/v1/security/ping-rate-limit"
Write-Host "docker compose exec api alembic heads"