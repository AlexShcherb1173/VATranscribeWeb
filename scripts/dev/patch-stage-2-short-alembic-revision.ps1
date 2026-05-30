$ErrorActionPreference = "Stop"

$Root = "D:\DevProject\PythonProject\VATranscribeWeb"

if (-not (Test-Path $Root)) {
    throw "Project root not found: $Root"
}

Set-Location $Root

$OldPath = "alembic\versions\20260529_0001_security_privacy_foundation.py"
$NewPath = "alembic\versions\20260529_sec_priv_found.py"

if (-not (Test-Path $OldPath)) {
    throw "Migration file not found: $OldPath"
}

$Text = Get-Content -Raw -Encoding UTF8 $OldPath

$Text = $Text.Replace(
    "revision = '20260529_0001_security_privacy_foundation'",
    "revision = '20260529_sec_priv_found'"
)

Set-Content -Encoding UTF8 -Path $NewPath -Value $Text

if ($OldPath -ne $NewPath) {
    Remove-Item $OldPath -Force
}

Write-Host "Alembic revision shortened:"
Write-Host "  old: 20260529_0001_security_privacy_foundation"
Write-Host "  new: 20260529_sec_priv_found"
Write-Host ""
Write-Host "Next:"
Write-Host "docker compose exec api alembic heads"
Write-Host "docker compose exec api alembic upgrade head"
Write-Host "docker compose exec api alembic current"