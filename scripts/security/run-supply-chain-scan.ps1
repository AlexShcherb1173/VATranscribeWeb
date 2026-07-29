param(
    [string]$ReportDir = "reports/security"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $ProjectRoot

New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null

function Test-Command {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

pwsh -ExecutionPolicy Bypass -File .\scripts\security\check-lockfiles.ps1

if (Test-Command "pip-audit") {
    pip-audit --local --progress-spinner off --format json --output (Join-Path $ReportDir "pip-audit.json")
}
else {
    Write-Host "[WARN] pip-audit is not installed. Install with: python -m pip install pip-audit" -ForegroundColor Yellow
}

if (Test-Command "npm") {
    npm audit --workspaces --audit-level=high --json | Set-Content -LiteralPath (Join-Path $ReportDir "npm-audit.json") -Encoding UTF8
}
else {
    Write-Host "[WARN] npm is not installed" -ForegroundColor Yellow
}

if (Test-Command "trivy") {
    trivy fs --scanners vuln,config,secret --severity HIGH,CRITICAL --exit-code 1 --ignore-unfixed --format table . | Tee-Object -FilePath (Join-Path $ReportDir "trivy-fs.txt")
}
else {
    Write-Host "[WARN] Trivy is not installed. See docs/security/supply-chain-security-scan.md" -ForegroundColor Yellow
}

if (Test-Command "gitleaks") {
    gitleaks dir . --config .gitleaks.local.toml --redact=100 --exit-code 1 --report-format json --report-path (Join-Path $ReportDir "gitleaks.json")
}
else {
    Write-Host "[WARN] Gitleaks is not installed. See docs/security/supply-chain-security-scan.md" -ForegroundColor Yellow
}

if (Test-Command "syft") {
    syft . -o "spdx-json=$(Join-Path $ReportDir 'sbom.spdx.json')"
}
else {
    Write-Host "[INFO] Syft is optional for local runs. SBOM generation is documented and enabled in CI." -ForegroundColor Cyan
}

Write-Host "[OK] Supply-chain scan completed" -ForegroundColor Green
