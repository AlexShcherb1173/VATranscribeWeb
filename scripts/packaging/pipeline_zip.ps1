$files = @(
  "apps/api/app/models.py",
  "apps/api/app/schemas.py",
  "apps/api/app/routers/jobs.py",
  "apps/api/app/routers/media_assets.py",
  "apps/worker/app/tasks/jobs.py",
  "packages/core/vatranscribe_core/storage.py",
  "packages/core/vatranscribe_core/download_engine.py",
  "apps/web/src/entities/job/model/types.ts",
  "apps/web/src/entities/media-file/model/types.ts",
  "apps/web/src/features/jobs/ui/JobDetailsCard.tsx",
  "apps/web/src/features/jobs/ui/JobActions.tsx",
  "apps/web/src/shared/api/files.ts"
)

$tempRoot = "__zip_temp_storage_pipeline"

# очистка
if (Test-Path $tempRoot) {
    Remove-Item $tempRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $tempRoot | Out-Null

foreach ($file in $files) {

    if (-not (Test-Path $file)) {
        Write-Host "NOT FOUND: $file"
        continue
    }

    $targetPath = Join-Path $tempRoot $file
    $targetDir = Split-Path $targetPath -Parent

    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

    Copy-Item $file $targetPath
}

if (Test-Path "storage_pipeline.zip") {
    Remove-Item "storage_pipeline.zip" -Force
}

Compress-Archive `
    -Path "$tempRoot\*" `
    -DestinationPath "storage_pipeline.zip"

# cleanup
Remove-Item $tempRoot -Recurse -Force

Write-Host ""
Write-Host "ZIP CREATED: storage_pipeline.zip"