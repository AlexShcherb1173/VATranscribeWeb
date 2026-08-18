param(
    [string]$EvidenceRoot = "reports/security/supply-chain-evidence"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $ProjectRoot

$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$EvidenceDir = Join-Path $EvidenceRoot $Timestamp
$RawDir = Join-Path $EvidenceDir "raw"
$SummaryFile = Join-Path $EvidenceDir "supply-chain-evidence.raw.md"
$SanitizedFile = Join-Path $EvidenceDir "supply-chain-evidence.sanitized.md"
$TriageFile = Join-Path $EvidenceDir "vulnerability-triage-high-critical.md"

New-Item -ItemType Directory -Path $RawDir -Force | Out-Null

function Test-CommandAvailable {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-Scan {
    param(
        [string]$Name,
        [string]$LogFile,
        [scriptblock]$Command
    )

    Write-Host "[SCAN] $Name" -ForegroundColor Cyan
    try {
        & $Command *> $LogFile
        $ExitCode = $LASTEXITCODE
        return $ExitCode
    }
    catch {
        $_ | Out-String | Add-Content -LiteralPath $LogFile -Encoding UTF8
        return 1
    }
}

function Status-Of {
    param([int]$ExitCode)
    if ($ExitCode -eq 0) { return "PASS" }
    return "FAIL"
}

function Tool-Status {
    param([string]$Name)
    if (Test-CommandAvailable $Name) { return "available" }
    return "missing"
}

$LockExit = Invoke-Scan "lockfile policy" (Join-Path $RawDir "check-lockfiles.log") {
    pwsh -ExecutionPolicy Bypass -File .\scripts\security\check-lockfiles.ps1
}

if (Test-CommandAvailable "pip-audit") {
    $PipExit = Invoke-Scan "pip-audit" (Join-Path $RawDir "pip-audit.log") {
        pip-audit --local --progress-spinner off --timeout 60 --format json --output (Join-Path $RawDir "pip-audit.json")
    }
}
else {
    $PipExit = 127
    "pip-audit not installed" | Set-Content -LiteralPath (Join-Path $RawDir "pip-audit.log") -Encoding UTF8
}

if (Test-CommandAvailable "npm") {
    Write-Host "[SCAN] npm audit" -ForegroundColor Cyan
    try {
        npm audit --workspaces --audit-level=high --json *> (Join-Path $RawDir "npm-audit.json")
        $NpmExit = $LASTEXITCODE
    }
    catch {
        $_ | Out-String | Add-Content -LiteralPath (Join-Path $RawDir "npm-audit.json") -Encoding UTF8
        $NpmExit = 1
    }
}
else {
    $NpmExit = 127
    "npm not installed" | Set-Content -LiteralPath (Join-Path $RawDir "npm-audit.json") -Encoding UTF8
}

if (Test-CommandAvailable "trivy") {
    $TrivyExit = Invoke-Scan "Trivy fs" (Join-Path $RawDir "trivy-fs.log") {
        trivy fs --timeout 30m --scanners vuln,misconfig,secret --severity HIGH,CRITICAL --exit-code 1 --ignore-unfixed --skip-dirs "**/node_modules" --format json --output (Join-Path $RawDir "trivy-fs.json") .
    }
}
else {
    $TrivyExit = 127
    "trivy not installed" | Set-Content -LiteralPath (Join-Path $RawDir "trivy-fs.log") -Encoding UTF8
}

if (Test-CommandAvailable "gitleaks") {
    $GitleaksExit = Invoke-Scan "Gitleaks" (Join-Path $RawDir "gitleaks.log") {
        gitleaks dir . --config .gitleaks.local.toml --redact=100 --exit-code 1 --report-format json --report-path (Join-Path $RawDir "gitleaks.json")
    }
}
else {
    $GitleaksExit = 127
    "gitleaks not installed" | Set-Content -LiteralPath (Join-Path $RawDir "gitleaks.log") -Encoding UTF8
}

if (Test-CommandAvailable "syft") {
    $SbomPath = Join-Path $RawDir "sbom.spdx.json"
    $SyftExit = Invoke-Scan "Syft SBOM" (Join-Path $RawDir "syft.log") {
        syft . -o "spdx-json=$SbomPath"
    }
}
else {
    $SyftExit = 127
    "syft not installed" | Set-Content -LiteralPath (Join-Path $RawDir "syft.log") -Encoding UTF8
}

$ReleaseDecision = "PASS"
if (($LockExit + $PipExit + $NpmExit + $TrivyExit + $GitleaksExit + $SyftExit) -ne 0) {
    $ReleaseDecision = "BLOCKED_OR_REQUIRES_TRIAGE"
}

$GitCommit = try { git rev-parse HEAD } catch { "unknown" }
$GitBranch = try { git branch --show-current } catch { "unknown" }

@"
# P3-07 Supply-chain evidence

Generated at UTC: $Timestamp
Git commit: $GitCommit
Git branch: $GitBranch
Evidence directory: $EvidenceDir

## Tool availability

| Tool | Status |
|---|---|
| pip-audit | $(Tool-Status "pip-audit") |
| npm | $(Tool-Status "npm") |
| Trivy | $(Tool-Status "trivy") |
| Gitleaks | $(Tool-Status "gitleaks") |
| Syft | $(Tool-Status "syft") |

## Scan results

| Gate | Status | Exit code | Raw report |
|---|---:|---:|---|
| Lockfile policy | $(Status-Of $LockExit) | $LockExit | raw/check-lockfiles.log |
| pip-audit | $(Status-Of $PipExit) | $PipExit | raw/pip-audit.json |
| npm audit | $(Status-Of $NpmExit) | $NpmExit | raw/npm-audit.json |
| Trivy filesystem/config/secret | $(Status-Of $TrivyExit) | $TrivyExit | raw/trivy-fs.json |
| Gitleaks secret scan | $(Status-Of $GitleaksExit) | $GitleaksExit | raw/gitleaks.json |
| Syft SBOM | $(Status-Of $SyftExit) | $SyftExit | raw/sbom.spdx.json |

## Release decision

Release decision: $ReleaseDecision

Critical and high findings block production release until fixed or explicitly triaged by the release owner. Medium findings require manual review. Low findings may be accepted with documented review.

## Secret handling notice

DO NOT commit raw scan reports, SBOM files, private registry URLs, tokens, credentials, runtime env files, or unreviewed Gitleaks findings to the repository.
"@ | Set-Content -LiteralPath $SummaryFile -Encoding UTF8

@"
# High/Critical vulnerability triage

Use this file for release-owner review. Store the completed copy outside Git unless it is fully sanitized.

| Finding | Scanner | Package/image/file | Severity | Reachability | User/data exposure | Fix/mitigation | Decision | Owner | Review date | Expiry date |
|---|---|---|---|---|---|---|---|---|---|---|
| _fill locally_ | _pip-audit/npm audit/Trivy/Gitleaks_ | _fill locally_ | _Critical/High_ | _yes/no/unknown_ | _yes/no/unknown_ | _fix version or mitigation_ | _fix/block/temporary exception_ | _owner_ | _YYYY-MM-DD_ | _YYYY-MM-DD or N/A_ |

Critical findings require a fix before public release unless the release owner records a formal no-exposure decision. High findings block release unless fixed or covered by a dated temporary exception.
"@ | Set-Content -LiteralPath $TriageFile -Encoding UTF8

pwsh -ExecutionPolicy Bypass -File .\scripts\security\redact-supply-chain-evidence.ps1 -InputFile $SummaryFile -OutputFile $SanitizedFile

Write-Host "[OK] Supply-chain evidence run completed" -ForegroundColor Green
Write-Host "[OK] Raw evidence directory: $RawDir" -ForegroundColor Green
Write-Host "[OK] Sanitized summary: $SanitizedFile" -ForegroundColor Green
Write-Host "[OK] Triage template: $TriageFile" -ForegroundColor Green

if ($ReleaseDecision -ne "PASS") {
    Write-Host "[BLOCKED] Supply-chain release gate requires triage. See $TriageFile" -ForegroundColor Red
    exit 1
}
