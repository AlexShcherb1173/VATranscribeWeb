$ErrorActionPreference = "Stop"

cd D:\DevProject\PythonProject\VATranscribe_clean

docker compose exec worker python -m pip install --no-cache-dir demucs torch torchaudio

docker compose restart worker

Write-Host "Demucs dependencies installed in the current worker container."
Write-Host "For persistent installation, add demucs, torch and torchaudio to the worker image requirements/Dockerfile."
