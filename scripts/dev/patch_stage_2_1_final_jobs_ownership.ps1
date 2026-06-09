$ErrorActionPreference = "Stop"

$Root = "D:\DevProject\PythonProject\VATranscribeWeb"
$JobsPath = Join-Path $Root "apps\api\app\routers\jobs.py"
$TestPath = Join-Path $Root "tests\security\test_file_ownership_static.py"

if (-not (Test-Path $JobsPath)) {
    throw "File not found: $JobsPath"
}

$Text = Get-Content -Raw -Encoding UTF8 $JobsPath
$Text = $Text -replace "`r`n", "`n"

$ImportLine = "from apps.api.app.services.access_control import get_user_media_asset_or_404"
$QuotaImport = "from apps.api.app.services.quota_service import assert_can_create_job, increment_jobs_used"

if ($Text -notmatch [regex]::Escape($ImportLine)) {
    if ($Text -notmatch [regex]::Escape($QuotaImport)) {
        throw "Could not find quota_service import in jobs.py"
    }

    $Text = $Text.Replace($QuotaImport, "$QuotaImport`n$ImportLine")
}

$OldBlock = @"
    assert_can_create_job(db, current_user, jobs_to_add=1)

    job = Job(
"@

$NewBlock = @"
    assert_can_create_job(db, current_user, jobs_to_add=1)

    if payload.transcription_media_asset_id:
        get_user_media_asset_or_404(
            db=db,
            current_user=current_user,
            media_asset_id=payload.transcription_media_asset_id,
        )

    job = Job(
"@

if ($Text.Contains($NewBlock)) {
    Write-Host "Ownership block already exists. No changes needed."
}
else {
    if (-not $Text.Contains($OldBlock)) {
        throw "Could not find exact insertion point in jobs.py"
    }

    $Text = $Text.Replace($OldBlock, $NewBlock)
    Set-Content -Encoding UTF8 -Path $JobsPath -Value $Text
    Write-Host "OK: ownership block inserted before Job(...)."
}

New-Item -ItemType Directory -Force -Path (Split-Path $TestPath -Parent) | Out-Null

@"
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_jobs_create_validates_transcription_media_asset_owner_before_job_creation():
    text = read("apps/api/app/routers/jobs.py")

    assert "from apps.api.app.services.access_control import get_user_media_asset_or_404" in text

    quota_marker = "assert_can_create_job(db, current_user, jobs_to_add=1)"
    helper_marker = "get_user_media_asset_or_404("
    ownership_marker = "media_asset_id=payload.transcription_media_asset_id"
    job_marker = "job = Job("

    quota_index = text.index(quota_marker)
    helper_index = text.index(helper_marker, quota_index)
    ownership_index = text.index(ownership_marker, quota_index)
    job_create_index = text.index(job_marker, quota_index)

    assert quota_index < helper_index < ownership_index < job_create_index


def test_media_assets_router_scopes_by_current_user():
    text = read("apps/api/app/routers/media_assets.py")
    assert "MediaAsset.user_id == current_user.id" in text


def test_transcripts_router_scopes_by_current_user():
    text = read("apps/api/app/routers/transcripts.py")
    assert "MediaAsset.user_id == current_user.id" in text


def test_export_artifacts_router_scopes_by_current_user():
    text = read("apps/api/app/routers/export_artifacts.py")
    assert "MediaAsset.user_id == current_user.id" in text


def test_transcription_job_creation_scopes_media_asset_by_current_user():
    text = read("apps/api/app/routers/transcriptions.py")
    assert "MediaAsset.user_id == current_user.id" in text
"@ | Set-Content -Encoding UTF8 $TestPath

Write-Host "OK: ownership test updated."
