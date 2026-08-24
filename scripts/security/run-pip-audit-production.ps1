param(
    [Parameter(Mandatory = $true)]
    [string]$OutputFile,

    [string]$DockerImage = "python:3.12-slim-bookworm",

    [string]$PipAuditVersion = "2.10.1"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (
    Resolve-Path (
        Join-Path $PSScriptRoot "..\.."
    )
).Path

$OutputFullPath = [System.IO.Path]::GetFullPath(
    $OutputFile
)

$OutputDir = Split-Path `
    -Parent `
    $OutputFullPath

$OutputName = Split-Path `
    -Leaf `
    $OutputFullPath

New-Item `
    -ItemType Directory `
    -Path $OutputDir `
    -Force |
    Out-Null

Remove-Item `
    -LiteralPath $OutputFullPath `
    -Force `
    -ErrorAction SilentlyContinue

$Docker = Get-Command `
    "docker.exe" `
    -ErrorAction SilentlyContinue

if ($null -eq $Docker) {
    $Docker = Get-Command `
        "docker" `
        -ErrorAction SilentlyContinue
}

if ($null -eq $Docker) {
    throw "Docker is required for production-aligned pip-audit."
}

$ContainerScript = @"
set -eu

python - <<'PY'
import sys

print(
    "PIP_AUDIT_RUNTIME_PYTHON="
    + sys.version.split()[0]
)

if sys.version_info[:2] != (3, 12):
    raise SystemExit(
        "pip-audit runtime must use Python 3.12"
    )
PY

python -m pip install \
  --disable-pip-version-check \
  --no-cache-dir \
  "pip-audit==$PipAuditVersion"

python -m pip_audit --version

cd /workspace

python -m pip_audit . \
  --strict \
  --progress-spinner off \
  --timeout 60 \
  --format json \
  --output "/out/$OutputName"
"@

$DockerArgs = @(
    "run",
    "--rm",
    "--mount",
    "type=bind,source=$ProjectRoot,target=/workspace,readonly",
    "--mount",
    "type=bind,source=$OutputDir,target=/out",
    $DockerImage,
    "sh",
    "-lc",
    $ContainerScript
)

& $Docker.Source @DockerArgs

$AuditExit = $LASTEXITCODE

if ($AuditExit -ne 0) {
    exit $AuditExit
}

if (
    -not (
        Test-Path `
            -LiteralPath $OutputFullPath
    )
) {
    throw "pip-audit completed without JSON output."
}

exit 0
