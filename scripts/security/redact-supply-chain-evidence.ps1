param(
    [Parameter(Mandatory = $true)]
    [string]$InputFile,

    [Parameter(Mandatory = $true)]
    [string]$OutputFile
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $InputFile)) {
    throw "Input file not found: $InputFile"
}

$OutputParent = Split-Path $OutputFile -Parent
if ($OutputParent -and -not (Test-Path $OutputParent)) {
    New-Item -ItemType Directory -Path $OutputParent -Force | Out-Null
}

$Content = Get-Content -LiteralPath $InputFile -Raw

$Content = $Content -replace '(?i)(token|secret|password|passwd|api[_-]?key|authorization|credential|private[_-]?key)([=: ]+)[^ ,;"'']+', '$1$2<redacted>'
$Content = $Content -replace '(https?://)[^/@\s]+:[^/@\s]+@', '$1<redacted>:<redacted>@'
$Content = $Content -replace '(registry\.npmjs\.org/)[^\s]+', '$1<redacted>'
$Content = $Content -replace '(/opt/vatranscribe/secrets/)[^\s]+', '$1<redacted>'
$Content = $Content -replace '(DATABASE_URL=).*', '$1<redacted>'
$Content = $Content -replace '(SENTRY_DSN=).*', '$1<redacted>'
$Content = $Content -replace '(NPM_TOKEN=).*', '$1<redacted>'
$Content = $Content -replace '(GITHUB_TOKEN=).*', '$1<redacted>'

$Content += @"

## Redaction notice

This is a sanitized evidence summary. DO NOT commit raw scanner outputs, SBOM files, private registry URLs, real credentials, runtime env files, or unreviewed secret findings to the repository.
"@

Set-Content -LiteralPath $OutputFile -Value $Content -Encoding UTF8
Write-Host "[OK] Redacted supply-chain evidence written: $OutputFile" -ForegroundColor Green
