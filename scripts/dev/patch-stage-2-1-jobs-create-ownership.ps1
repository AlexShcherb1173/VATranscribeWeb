$ErrorActionPreference = "Stop"

$Root = "D:\DevProject\PythonProject\VATranscribeWeb"

if (-not (Test-Path $Root)) {
    throw "Project root not found: $Root"
}

Set-Location $Root

$JobsPath = "apps\api\app\routers\jobs.py"

if (-not (Test-Path $JobsPath)) {
    throw "File not found: $JobsPath"
}

$Text = Get-Content -Raw -Encoding UTF8 $JobsPath
$Text = $Text -replace "`r`n", "`n"

$ImportOld = "from apps.api.app.services.quota_service import assert_can_create_job, increment_jobs_used"
$ImportNew = "from apps.api.app.services.quota_service import assert_can_create_job, increment_jobs_used`nfrom apps.api.app.services.access_control import get_user_media_asset_or_404"

if ($Text -notmatch "from apps\.api\.app\.services\.access_control import get_user_media_asset_or_404") {
    if ($Text.Contains($ImportOld)) {
        $Text = $Text.Replace($ImportOld, $ImportNew)
    } else {
        throw "Could not find quota_service import in jobs.py"
    }
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

if ($Text -notmatch "media_asset_id=payload\.transcription_media_asset_id") {
    if ($Text.Contains($OldBlock)) {
        $Text = $Text.Replace($OldBlock, $NewBlock)
    } else {
        throw "Could not find create_job insertion point in jobs.py"
    }
}

Set-Content -Encoding UTF8 -Path $JobsPath -Value $Text

Write-Host "Patched jobs.py: POST /jobs now validates transcription_media_asset_id ownership."
Write-Host ""
Write-Host "Next:"
Write-Host "python -m pytest tests/security/test_file_ownership_static.py"
Write-Host "docker compose restart api"
Write-Host "curl http://localhost:8000/api/v1/health/live"