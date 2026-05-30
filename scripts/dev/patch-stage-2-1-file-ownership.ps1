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

Write-Host "Stage 2.1: File Ownership and User Isolation patch..."

# ============================================================
# Centralized access control service
# ============================================================

Write-TextFile "apps/api/app/services/access_control.py" @(
    "from __future__ import annotations",
    "",
    "from fastapi import HTTPException, status",
    "from sqlalchemy import select",
    "from sqlalchemy.orm import Session, selectinload",
    "",
    "from apps.api.app.models import ExportArtifact, Job, MediaAsset, Transcript, User",
    "",
    "",
    "def not_found(entity: str, entity_id: str) -> HTTPException:",
    "    return HTTPException(",
    "        status_code=status.HTTP_404_NOT_FOUND,",
    "        detail=f""{entity} '{entity_id}' not found"",",
    "    )",
    "",
    "",
    "def get_user_job_or_404(",
    "    db: Session,",
    "    current_user: User,",
    "    job_id: str,",
    ") -> Job:",
    "    stmt = select(Job).where(",
    "        Job.id == job_id,",
    "        Job.user_id == current_user.id,",
    "    )",
    "    item = db.scalar(stmt)",
    "",
    "    if item is None:",
    "        raise not_found('Job', job_id)",
    "",
    "    return item",
    "",
    "",
    "def get_user_media_asset_or_404(",
    "    db: Session,",
    "    current_user: User,",
    "    media_asset_id: str,",
    ") -> MediaAsset:",
    "    stmt = select(MediaAsset).where(",
    "        MediaAsset.id == media_asset_id,",
    "        MediaAsset.user_id == current_user.id,",
    "    )",
    "    item = db.scalar(stmt)",
    "",
    "    if item is None:",
    "        raise not_found('Media asset', media_asset_id)",
    "",
    "    return item",
    "",
    "",
    "def get_user_transcript_or_404(",
    "    db: Session,",
    "    current_user: User,",
    "    transcript_id: str,",
    ") -> Transcript:",
    "    stmt = (",
    "        select(Transcript)",
    "        .join(MediaAsset, Transcript.media_asset_id == MediaAsset.id)",
    "        .options(",
    "            selectinload(Transcript.media_asset),",
    "            selectinload(Transcript.job),",
    "            selectinload(Transcript.segments),",
    "            selectinload(Transcript.export_artifacts),",
    "        )",
    "        .where(",
    "            Transcript.id == transcript_id,",
    "            MediaAsset.user_id == current_user.id,",
    "        )",
    "    )",
    "    item = db.scalar(stmt)",
    "",
    "    if item is None:",
    "        raise not_found('Transcript', transcript_id)",
    "",
    "    return item",
    "",
    "",
    "def get_user_export_artifact_or_404(",
    "    db: Session,",
    "    current_user: User,",
    "    artifact_id: str,",
    ") -> ExportArtifact:",
    "    stmt = (",
    "        select(ExportArtifact)",
    "        .join(Transcript, ExportArtifact.transcript_id == Transcript.id)",
    "        .join(MediaAsset, Transcript.media_asset_id == MediaAsset.id)",
    "        .options(",
    "            selectinload(ExportArtifact.transcript).selectinload(Transcript.media_asset),",
    "        )",
    "        .where(",
    "            ExportArtifact.id == artifact_id,",
    "            MediaAsset.user_id == current_user.id,",
    "        )",
    "    )",
    "    item = db.scalar(stmt)",
    "",
    "    if item is None:",
    "        raise not_found('Export artifact', artifact_id)",
    "",
    "    return item"
)

# ============================================================
# Patch jobs.py:
# - import get_user_media_asset_or_404
# - validate payload.transcription_media_asset_id in generic POST /jobs
# ============================================================

$JobsPath = "apps\api\app\routers\jobs.py"

if (-not (Test-Path $JobsPath)) {
    throw "File not found: $JobsPath"
}

$Text = Get-Content -Raw -Encoding UTF8 $JobsPath
$Text = $Text -replace "`r`n", "`n"

$ImportOld = "from apps.api.app.services.quota_service import assert_can_create_job, increment_jobs_used"
$ImportNew = "from apps.api.app.services.quota_service import assert_can_create_job, increment_jobs_used`nfrom apps.api.app.services.access_control import get_user_media_asset_or_404"

if ($Text -notmatch "get_user_media_asset_or_404") {
    $Text = $Text.Replace($ImportOld, $ImportNew)
}

$OldBlock = "    assert_can_create_job(db, current_user, jobs_to_add=1)`n`n    job = Job("
$NewBlock = "    assert_can_create_job(db, current_user, jobs_to_add=1)`n`n    if payload.transcription_media_asset_id:`n        get_user_media_asset_or_404(`n            db=db,`n            current_user=current_user,`n            media_asset_id=payload.transcription_media_asset_id,`n        )`n`n    job = Job("

if ($Text -notmatch "media_asset_id=payload.transcription_media_asset_id") {
    if ($Text.Contains($OldBlock)) {
        $Text = $Text.Replace($OldBlock, $NewBlock)
    } else {
        throw "Could not find create_job insertion point in jobs.py"
    }
}

Set-Content -Encoding UTF8 -Path $JobsPath -Value $Text

# ============================================================
# Static regression tests
# ============================================================

Write-TextFile "tests/security/test_file_ownership_static.py" @(
    "from pathlib import Path",
    "",
    "",
    "ROOT = Path(__file__).resolve().parents[2]",
    "",
    "",
    "def read(path: str) -> str:",
    "    return (ROOT / path).read_text(encoding='utf-8')",
    "",
    "",
    "def test_jobs_create_validates_transcription_media_asset_owner():",
    "    text = read('apps/api/app/routers/jobs.py')",
    "    assert 'get_user_media_asset_or_404' in text",
    "    assert 'media_asset_id=payload.transcription_media_asset_id' in text",
    "",
    "",
    "def test_media_assets_router_scopes_by_current_user():",
    "    text = read('apps/api/app/routers/media_assets.py')",
    "    assert 'MediaAsset.user_id == current_user.id' in text",
    "",
    "",
    "def test_transcripts_router_scopes_by_current_user():",
    "    text = read('apps/api/app/routers/transcripts.py')",
    "    assert 'MediaAsset.user_id == current_user.id' in text",
    "",
    "",
    "def test_export_artifacts_router_scopes_by_current_user():",
    "    text = read('apps/api/app/routers/export_artifacts.py')",
    "    assert 'MediaAsset.user_id == current_user.id' in text",
    "",
    "",
    "def test_transcription_job_creation_scopes_media_asset_by_current_user():",
    "    text = read('apps/api/app/routers/transcriptions.py')",
    "    assert 'MediaAsset.user_id == current_user.id' in text"
)

# ============================================================
# Documentation
# ============================================================

Write-TextFile "docs/security/file-ownership.md" @(
    "# File Ownership and User Isolation",
    "",
    "Every user-owned object must be selected with current_user.id.",
    "",
    "Protected object groups:",
    "- jobs",
    "- media_assets",
    "- transcripts",
    "- export_artifacts",
    "- uploads",
    "- downloads",
    "- transcription jobs",
    "",
    "Required rule:",
    "Do not fetch user-owned objects by id only.",
    "",
    "Correct pattern:",
    "select(Entity).where(Entity.id == id, Entity.user_id == current_user.id)",
    "",
    "For indirect ownership:",
    "ExportArtifact -> Transcript -> MediaAsset -> user_id",
    "",
    "Generic job creation must validate transcription_media_asset_id before creating a job."
)

Write-Host "Stage 2.1 file ownership patch completed."
Write-Host ""
Write-Host "Next:"
Write-Host "docker compose restart api"
Write-Host "curl http://localhost:8000/api/v1/health/live"
Write-Host "docker compose exec api python -m pytest tests/security tests/privacy"