from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _as_path(output_path: str | Path) -> Path:
    path = Path(str(output_path).replace("\\", "/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _format_timestamp(seconds: int | float) -> str:
    total_ms = int(float(seconds) * 1000)
    hours = total_ms // 3_600_000
    minutes = (total_ms % 3_600_000) // 60_000
    secs = (total_ms % 60_000) // 1000
    millis = total_ms % 1000
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def _format_vtt_timestamp(seconds: int | float) -> str:
    return _format_timestamp(seconds).replace(",", ".")


def write_txt(output_path: str | Path, text: str) -> Path:
    path = _as_path(output_path)
    path.write_text(text or "", encoding="utf-8")
    return path


def write_srt(output_path: str | Path, segments: list[dict[str, Any]]) -> Path:
    path = _as_path(output_path)

    blocks: list[str] = []

    for index, segment in enumerate(segments, start=1):
        start = segment.get("start_sec", segment.get("start", 0)) or 0
        end = segment.get("end_sec", segment.get("end", 0)) or 0
        text = (segment.get("text") or "").strip()

        if not text:
            continue

        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{_format_timestamp(start)} --> {_format_timestamp(end)}",
                    text,
                ]
            )
        )

    path.write_text("\n\n".join(blocks).strip() + "\n", encoding="utf-8")
    return path


def write_vtt(output_path: str | Path, segments: list[dict[str, Any]]) -> Path:
    path = _as_path(output_path)

    blocks: list[str] = ["WEBVTT", ""]

    for segment in segments:
        start = segment.get("start_sec", segment.get("start", 0)) or 0
        end = segment.get("end_sec", segment.get("end", 0)) or 0
        text = (segment.get("text") or "").strip()

        if not text:
            continue

        blocks.append(
            "\n".join(
                [
                    f"{_format_vtt_timestamp(start)} --> {_format_vtt_timestamp(end)}",
                    text,
                ]
            )
        )

    path.write_text("\n\n".join(blocks).strip() + "\n", encoding="utf-8")
    return path


def write_json(output_path: str | Path, payload: dict[str, Any]) -> Path:
    path = _as_path(output_path)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path