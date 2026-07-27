$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $ProjectRoot

function Require-File {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file is missing: $Path"
    }
}

Require-File "pyproject.toml"
Require-File "package.json"
Require-File "package-lock.json"
Require-File "apps/web/package.json"
Require-File "apps/marketing/package.json"
Require-File "infra/docker/api.Dockerfile"
Require-File "infra/docker/worker.Dockerfile"
Require-File "infra/docker/web.Dockerfile"
Require-File "infra/compose/docker-compose.prod.yml"

$Untracked = git ls-files --others --exclude-standard |
    Select-String -Pattern '(^|/)package-lock\.json$|(^|/)poetry\.lock$|(^|/)requirements.*\.txt$'

if ($Untracked) {
    Write-Host "[WARN] Untracked dependency lock/manifests detected:" -ForegroundColor Yellow
    $Untracked | ForEach-Object { Write-Host $_.Line -ForegroundColor Yellow }
    throw "Track or remove dependency lock/manifests before release."
}

Write-Host "[OK] Lockfile and manifest policy passed" -ForegroundColor Green
