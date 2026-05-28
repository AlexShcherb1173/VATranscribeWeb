from __future__ import annotations

import subprocess
from pathlib import Path

from apps.api.app.config import get_settings


def _ffmpeg_path() -> str:
    settings = get_settings()
    return str(getattr(settings, "ffmpeg_path", "ffmpeg"))


def extract_audio_for_transcription(input_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        _ffmpeg_path(),
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]

    subprocess.run(command, check=True, capture_output=True, text=True)
    return output_path
