$ErrorActionPreference = "Stop"

# ============================================================
# VATranscribe_clean -> VATranscribeWeb migration script
# ============================================================

$SourceRoot = "D:\DevProject\PythonProject\VATranscribe_clean"
$TargetRoot = "D:\DevProject\PythonProject\VATranscribeWeb"

# true  = существующие файлы будут заменяться
# false = существующие файлы останутся, будут копироваться только отсутствующие
$OverwriteExisting = $true

# true = перед заменой существующие папки/файлы сохраняются в _migration_backup
$CreateBackup = $true

$BackupRoot = Join-Path $TargetRoot "_migration_backup"

# ============================================================
# Checks
# ============================================================

if (-not (Test-Path $SourceRoot)) {
    throw "Source root not found: $SourceRoot"
}

if (-not (Test-Path $TargetRoot)) {
    throw "Target root not found: $TargetRoot"
}

Set-Location $TargetRoot

Write-Host ""
Write-Host "Source: $SourceRoot"
Write-Host "Target: $TargetRoot"
Write-Host "Overwrite existing: $OverwriteExisting"
Write-Host "Create backup: $CreateBackup"
Write-Host ""

# ============================================================
# Exclude rules
# ============================================================

$ExcludeDirs = @(
    ".git",
    ".idea",
    ".vscode",
    ".junie",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    "dist",
    "build",
    "coverage",
    "htmlcov",
    "storage",
    "data",
    "zip",
    "tmp",
    "temp",
    ".cache",
    ".turbo",
    ".parcel-cache",
    "docker-data",
    "docker-volumes",
    "pgdata",
    "redis-data",
    "vatranscribe.egg-info"
)

$ExcludeFilePatterns = @(
    "*.zip",
    "*.rar",
    "*.7z",
    "*.tar",
    "*.gz",
    "*.mp4",
    "*.mp3",
    "*.wav",
    "*.mkv",
    "*.avi",
    "*.mov",
    "*.webm",
    "*.log",
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    ".env",
    ".env.local",
    ".env.*.local"
)

# ============================================================
# Helpers
# ============================================================

function Test-IsExcludedDirectoryName {
    param([string]$Name)

    foreach ($Excluded in $ExcludeDirs) {
        if ($Name -ieq $Excluded) {
            return $true
        }
    }

    return $false
}

function Test-IsExcludedFileName {
    param([string]$Name)

    foreach ($Pattern in $ExcludeFilePatterns) {
        if ($Name -like $Pattern) {
            return $true
        }
    }

    return $false
}

function Ensure-Directory {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Backup-Path {
    param(
        [string]$TargetPath,
        [string]$RelativePath
    )

    if (-not $CreateBackup) {
        return
    }

    if (-not (Test-Path $TargetPath)) {
        return
    }

    $BackupPath = Join-Path $BackupRoot $RelativePath
    $BackupDir = Split-Path $BackupPath -Parent

    Ensure-Directory $BackupDir

    if (Test-Path $BackupPath) {
        Remove-Item $BackupPath -Recurse -Force
    }

    Copy-Item -LiteralPath $TargetPath -Destination $BackupPath -Recurse -Force
}

function Copy-DirectorySafe {
    param(
        [string]$SourcePath,
        [string]$TargetPath,
        [string]$DisplayName
    )

    if (-not (Test-Path $SourcePath)) {
        Write-Host "SKIP missing: $DisplayName"
        return
    }

    Write-Host "COPY dir: $DisplayName"

    $RelativeBackupPath = $DisplayName

    if ((Test-Path $TargetPath) -and $OverwriteExisting) {
        Backup-Path -TargetPath $TargetPath -RelativePath $RelativeBackupPath
    }

    Ensure-Directory $TargetPath

    $Files = Get-ChildItem -LiteralPath $SourcePath -Recurse -File -Force | Where-Object {
        $relative = $_.FullName.Substring($SourcePath.Length).TrimStart("\")
        $parts = $relative -split "\\"

        $excludedByDir = $false
        foreach ($part in $parts) {
            if (Test-IsExcludedDirectoryName $part) {
                $excludedByDir = $true
                break
            }
        }

        (-not $excludedByDir) -and (-not (Test-IsExcludedFileName $_.Name))
    }

    foreach ($File in $Files) {
        $RelativeFile = $File.FullName.Substring($SourcePath.Length).TrimStart("\")
        $DestinationFile = Join-Path $TargetPath $RelativeFile
        $DestinationDir = Split-Path $DestinationFile -Parent

        Ensure-Directory $DestinationDir

        if ((Test-Path $DestinationFile) -and (-not $OverwriteExisting)) {
            continue
        }

        if ((Test-Path $DestinationFile) -and $OverwriteExisting) {
            $BackupRelative = Join-Path $DisplayName $RelativeFile
            Backup-Path -TargetPath $DestinationFile -RelativePath $BackupRelative
        }

        Copy-Item -LiteralPath $File.FullName -Destination $DestinationFile -Force
    }
}

function Copy-FileSafe {
    param(
        [string]$SourcePath,
        [string]$TargetPath,
        [string]$DisplayName
    )

    if (-not (Test-Path $SourcePath)) {
        Write-Host "SKIP missing: $DisplayName"
        return
    }

    if (Test-IsExcludedFileName (Split-Path $SourcePath -Leaf)) {
        Write-Host "SKIP excluded: $DisplayName"
        return
    }

    if ((Test-Path $TargetPath) -and (-not $OverwriteExisting)) {
        Write-Host "SKIP exists: $DisplayName"
        return
    }

    Write-Host "COPY file: $DisplayName"

    $TargetDir = Split-Path $TargetPath -Parent
    Ensure-Directory $TargetDir

    if ((Test-Path $TargetPath) -and $OverwriteExisting) {
        Backup-Path -TargetPath $TargetPath -RelativePath $DisplayName
    }

    Copy-Item -LiteralPath $SourcePath -Destination $TargetPath -Force
}

# ============================================================
# Directories to migrate
# ============================================================

$DirectoryMappings = @(
    @{ From = "apps\api";        To = "apps\api" },
    @{ From = "apps\web";        To = "apps\web" },
    @{ From = "apps\worker";     To = "apps\worker" },
    @{ From = "apps\desktop";    To = "apps\desktop" },
    @{ From = "packages\core";   To = "packages\core" },
    @{ From = "infra";           To = "infra" },
    @{ From = "alembic";         To = "alembic" },
    @{ From = "tests";           To = "tests" },
    @{ From = ".github\workflows"; To = ".github\workflows" }
)

foreach ($Map in $DirectoryMappings) {
    $FromPath = Join-Path $SourceRoot $Map.From
    $ToPath = Join-Path $TargetRoot $Map.To

    Copy-DirectorySafe `
        -SourcePath $FromPath `
        -TargetPath $ToPath `
        -DisplayName $Map.To
}

# ============================================================
# Root config files to migrate
# ============================================================

$RootFiles = @(
    ".dockerignore",
    ".env.example",
    ".gitignore",
    ".npmrc",
    "alembic.ini",
    "docker-compose.yml",
    "Makefile",
    "package.json",
    "package-lock.json",
    "pyproject.toml",
    "turbo.json",
    "README.md"
)

foreach ($FileName in $RootFiles) {
    $FromPath = Join-Path $SourceRoot $FileName
    $ToPath = Join-Path $TargetRoot $FileName

    Copy-FileSafe `
        -SourcePath $FromPath `
        -TargetPath $ToPath `
        -DisplayName $FileName
}

# ============================================================
# Optional old maintenance files
# They are not copied to root. They go to scripts/maintenance or scripts/migrations.
# ============================================================

$OptionalFileMappings = @(
    @{ From = "install-demucs-in-worker.ps1";       To = "scripts\maintenance\install-demucs-in-worker.ps1" },
    @{ From = "requirements-demucs.txt";           To = "scripts\maintenance\requirements-demucs.txt" },
    @{ From = "requirements-worker-demucs.txt";    To = "scripts\maintenance\requirements-worker-demucs.txt" },
    @{ From = "fix-large-upload-bigint.sql";       To = "scripts\migrations\fix-large-upload-bigint.sql" },
    @{ From = "pipeline_zip.ps1";                  To = "scripts\packaging\pipeline_zip.ps1" }
)

foreach ($Map in $OptionalFileMappings) {
    $FromPath = Join-Path $SourceRoot $Map.From
    $ToPath = Join-Path $TargetRoot $Map.To

    Copy-FileSafe `
        -SourcePath $FromPath `
        -TargetPath $ToPath `
        -DisplayName $Map.To
}

# ============================================================
# Ensure new target-only structure remains
# ============================================================

$TargetOnlyDirs = @(
    "apps\marketing",
    "apps\admin",
    "packages\shared-types",
    "packages\sdk",
    "docs\architecture",
    "docs\api",
    "docs\billing",
    "docs\monetization",
    "docs\security",
    "docs\privacy",
    "docs\legal",
    "docs\desktop",
    "docs\deployment",
    "docs\roadmap",
    "scripts\dev",
    "scripts\reports",
    "scripts\security",
    "scripts\backup",
    "tests\billing",
    "tests\monetization",
    "tests\security",
    "tests\privacy",
    "tests\compliance",
    "tests\integration"
)

foreach ($Dir in $TargetOnlyDirs) {
    $Path = Join-Path $TargetRoot $Dir
    Ensure-Directory $Path

    $Gitkeep = Join-Path $Path ".gitkeep"
    if (-not (Test-Path $Gitkeep)) {
        New-Item -ItemType File -Force -Path $Gitkeep | Out-Null
    }
}

# ============================================================
# Summary
# ============================================================

Write-Host ""
Write-Host "Migration completed."
Write-Host ""

if ($CreateBackup) {
    Write-Host "Backup directory:"
    Write-Host $BackupRoot
    Write-Host ""
}

Write-Host "Recommended next commands:"
Write-Host "git status"
Write-Host "git diff --stat"
Write-Host ""
Write-Host "Then inspect changed files before commit."