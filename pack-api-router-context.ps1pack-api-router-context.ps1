$ErrorActionPreference = "Stop"

$Root = "D:\DevProject\PythonProject\VATranscribeWeb"
$OutDir = Join-Path $Root "_debug_packs"
$PackName = "api_router_context_pack.zip"
$PackPath = Join-Path $OutDir $PackName
$TempDir = Join-Path $OutDir "api_router_context_pack"

if (-not (Test-Path $Root)) {
    throw "Project root not found: $Root"
}

Set-Location $Root

if (Test-Path $TempDir) {
    Remove-Item $TempDir -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Copy-IfExists {
    param(
        [string]$RelativePath
    )

    $SourcePath = Join-Path $Root $RelativePath
    $TargetPath = Join-Path $TempDir $RelativePath

    if (-not (Test-Path $SourcePath)) {
        Write-Host "SKIP missing: $RelativePath"
        return
    }

    $TargetParent = Split-Path $TargetPath -Parent
    if ($TargetParent -and -not (Test-Path $TargetParent)) {
        New-Item -ItemType Directory -Force -Path $TargetParent | Out-Null
    }

    if ((Get-Item $SourcePath).PSIsContainer) {
        Copy-Item -LiteralPath $SourcePath -Destination $TargetPath -Recurse -Force
    } else {
        Copy-Item -LiteralPath $SourcePath -Destination $TargetPath -Force
    }

    Write-Host "COPIED: $RelativePath"
}

# Core app entry/config
Copy-IfExists "apps\api\app\main.py"
Copy-IfExists "apps\api\app\config.py"
Copy-IfExists "apps\api\app\database.py"
Copy-IfExists "apps\api\app\models.py"
Copy-IfExists "apps\api\app\schemas.py"

# Router aggregator and routers
Copy-IfExists "apps\api\app\routers"

# Schemas/models packages if project uses folders instead of single files
Copy-IfExists "apps\api\app\schemas"
Copy-IfExists "apps\api\app\models"

# New stage 2 files if already generated
Copy-IfExists "apps\api\app\security"
Copy-IfExists "apps\api\app\services"

# Alembic context
Copy-IfExists "alembic.ini"
Copy-IfExists "alembic\env.py"
Copy-IfExists "alembic\versions"

# Project dependency/config context
Copy-IfExists "pyproject.toml"
Copy-IfExists "docker-compose.yml"

# Generate tree snapshots
$TreeFile = Join-Path $TempDir "TREE_API_APP.txt"
tree "$Root\apps\api\app" /F | Out-File -Encoding UTF8 $TreeFile

$RoutersGrepFile = Join-Path $TempDir "ROUTERS_SEARCH.txt"
Get-ChildItem "$Root\apps\api\app" -Recurse -Filter *.py |
    Select-String -Pattern "include_router|APIRouter|router =" |
    Select-Object Path, LineNumber, Line |
    Out-File -Encoding UTF8 $RoutersGrepFile

$AlembicHeadsFile = Join-Path $TempDir "ALEMBIC_FILES.txt"
Get-ChildItem "$Root\alembic\versions" -Filter *.py -ErrorAction SilentlyContinue |
    Select-Object Name, FullName |
    Out-File -Encoding UTF8 $AlembicHeadsFile

if (Test-Path $PackPath) {
    Remove-Item $PackPath -Force
}

Compress-Archive -Path (Join-Path $TempDir "*") -DestinationPath $PackPath -Force

Write-Host ""
Write-Host "Archive created:"
Write-Host $PackPath
Write-Host ""
Write-Host "Send this file:"
Write-Host $PackPath