from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def transcribe_media(
    *,
    audio_path: Path,
    model_name: str,
    language: str | None = None,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    from faster_whisper import WhisperModel

    if not audio_path.exists() or not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if progress_callback is not None:
        progress_callback({"stage": "load_model", "message": "Loading transcription model"})

    model = WhisperModel(model_name, device="cpu", compute_type="int8")

    if progress_callback is not None:
        progress_callback({"stage": "transcribe", "message": "Starting transcription"})

    segments_iter, info = model.transcribe(str(audio_path), language=language or None, vad_filter=True)
    total_duration = float(getattr(info, "duration", 0) or 0)

    full_text_parts: list[str] = []
    segments: list[dict[str, Any]] = []

    for index, segment in enumerate(segments_iter):
        text = (segment.text or "").strip()
        if text:
            full_text_parts.append(text)
        segments.append(
            {
                "start_sec": int(segment.start),
                "end_sec": int(segment.end),
                "text": text,
                "speaker_label": None,
                "confidence": None,
                "order_index": index,
            }
        )

        if progress_callback is not None:
            progress_callback(
                {
                    "stage": "transcribe",
                    "index": index,
                    "end_sec": float(segment.end or 0),
                    "duration_sec": total_duration,
                    "message": f"Transcribed segment {index + 1}",
                }
            )

    return {
        "engine": "faster_whisper",
        "language": getattr(info, "language", None) or language or "unknown",
        "model_name": model_name,
        "full_text": "\n".join(full_text_parts).strip(),
        "segments": segments,
    }
