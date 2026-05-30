from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import ExportArtifact, MediaAsset, Transcript, User
from apps.api.app.services.quota_service import sync_storage_usage_from_media_assets
from packages.core.vatranscribe_core.storage import resolve_storage_path, to_storage_relative_path

router = APIRouter(prefix="/transcripts", tags=["Transcripts"])

SUBTITLE_FORMATS = {"srt", "vtt", "subtitle_txt"}


class SubtitleGenerateRequest(BaseModel):
    formats: list[str] = Field(default_factory=lambda: ["srt", "vtt"])
    overwrite: bool = True


def _media_asset_payload(item: MediaAsset | None) -> dict[str, Any] | None:
    if item is None:
        return None

    return {
        "id": item.id,
        "kind": item.kind,
        "original_name": item.original_name,
        "stored_name": item.stored_name,
        "mime_type": item.mime_type,
        "extension": item.extension,
        "size_bytes": item.size_bytes,
        "duration_sec": item.duration_sec,
        "path": item.path,
        "checksum_sha256": item.checksum_sha256,
        "created_at": item.created_at,
        "download_url": f"/media-assets/{item.id}/download",
    }


def _source_file_name(item: Transcript) -> str | None:
    media_asset = item.media_asset

    if media_asset is None:
        return None

    return (
        media_asset.original_name
        or media_asset.stored_name
        or Path(media_asset.path or "").name
        or None
    )


def _display_name(item: Transcript) -> str:
    return (
        _source_file_name(item)
        or getattr(item.job, "title", None)
        or item.id
    )


def _segment_payload(segment) -> dict[str, Any]:
    return {
        "id": segment.id,
        "transcript_id": segment.transcript_id,
        "start_sec": segment.start_sec,
        "end_sec": segment.end_sec,
        "text": segment.text,
        "speaker_label": segment.speaker_label,
        "confidence": segment.confidence,
        "order_index": segment.order_index,
    }


def _export_payload(item: ExportArtifact) -> dict[str, Any]:
    return {
        "id": item.id,
        "transcript_id": item.transcript_id,
        "format": item.format,
        "path": item.path,
        "size_bytes": item.size_bytes,
        "created_at": item.created_at,
        "download_url": f"/transcripts/export-artifacts/{item.id}/download",
    }


def _build_transcript_response(
    item: Transcript,
    *,
    include_segments: bool = True,
    include_exports: bool = True,
) -> dict[str, Any]:
    source_file_name = _source_file_name(item)
    display_name = _display_name(item)

    return {
        "id": item.id,
        "job_id": item.job_id,
        "media_asset_id": item.media_asset_id,
        "media_asset": _media_asset_payload(item.media_asset),
        "source_file_name": source_file_name,
        "display_name": display_name,
        "language": item.language,
        "model_name": item.model_name,
        "engine": item.engine,
        "full_text": item.full_text,
        "duration_sec": getattr(item, "duration_sec", None),
        "segments_count": getattr(item, "segments_count", None),
        "coverage_sec": getattr(item, "coverage_sec", None),
        "coverage_ratio": getattr(item, "coverage_ratio", None),
        "quality_status": getattr(item, "quality_status", None),
        "quality_warning": getattr(item, "quality_warning", None),
        "created_at": item.created_at,
        "segments": [
            _segment_payload(segment)
            for segment in item.segments
        ] if include_segments else [],
        "exports": [
            _export_payload(artifact)
            for artifact in item.export_artifacts
        ] if include_exports else [],
    }


def _get_transcript_or_404(
    transcript_id: str,
    db: Session,
    current_user: User,
) -> Transcript:
    stmt = (
        select(Transcript)
        .join(MediaAsset, Transcript.media_asset_id == MediaAsset.id)
        .options(
            selectinload(Transcript.media_asset),
            selectinload(Transcript.job),
            selectinload(Transcript.segments),
            selectinload(Transcript.export_artifacts),
        )
        .where(
            Transcript.id == transcript_id,
            MediaAsset.user_id == current_user.id,
        )
    )
    item = db.scalar(stmt)

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcript '{transcript_id}' not found",
        )

    return item


def _get_export_artifact_or_404(
    artifact_id: str,
    db: Session,
    current_user: User,
) -> ExportArtifact:
    stmt = (
        select(ExportArtifact)
        .join(Transcript, ExportArtifact.transcript_id == Transcript.id)
        .join(MediaAsset, Transcript.media_asset_id == MediaAsset.id)
        .options(selectinload(ExportArtifact.transcript).selectinload(Transcript.media_asset))
        .where(
            ExportArtifact.id == artifact_id,
            MediaAsset.user_id == current_user.id,
        )
    )
    item = db.scalar(stmt)

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export artifact '{artifact_id}' not found",
        )

    return item


def _safe_stem(value: str | None, fallback: str) -> str:
    raw = (value or fallback or "transcript").strip()
    stem = Path(raw).stem.strip()
    stem = re.sub(r"[^\w\s.\-]+", "_", stem, flags=re.UNICODE)
    stem = re.sub(r"\s+", "_", stem, flags=re.UNICODE)
    stem = re.sub(r"_+", "_", stem, flags=re.UNICODE)
    stem = stem.strip("._- ")
    return (stem or fallback or "transcript")[:140]


def _subtitle_timestamp_srt(seconds: float | int | None) -> str:
    total_ms = max(0, int(round(float(seconds or 0) * 1000)))
    ms = total_ms % 1000
    total_seconds = total_ms // 1000
    sec = total_seconds % 60
    total_minutes = total_seconds // 60
    minute = total_minutes % 60
    hour = total_minutes // 60
    return f"{hour:02d}:{minute:02d}:{sec:02d},{ms:03d}"


def _subtitle_timestamp_vtt(seconds: float | int | None) -> str:
    return _subtitle_timestamp_srt(seconds).replace(",", ".")


def _segment_rows(transcript: Transcript) -> list[dict[str, Any]]:
    rows = [
        {
            "start_sec": float(segment.start_sec or 0),
            "end_sec": float(segment.end_sec or 0),
            "text": (segment.text or "").strip(),
            "order_index": int(segment.order_index or 0),
        }
        for segment in transcript.segments
        if (segment.text or "").strip()
    ]

    if rows:
        return rows

    text = (transcript.full_text or "").strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript text is empty. Cannot generate subtitles.",
        )

    return [{"start_sec": 0.0, "end_sec": 0.0, "text": text, "order_index": 0}]


def _render_srt(rows: list[dict[str, Any]]) -> str:
    blocks: list[str] = []

    for index, row in enumerate(rows, start=1):
        start = _subtitle_timestamp_srt(row.get("start_sec"))
        end_value = row.get("end_sec")
        end = _subtitle_timestamp_srt(end_value if end_value and end_value > row.get("start_sec", 0) else row.get("start_sec", 0) + 3)
        text = str(row.get("text") or "").strip()
        blocks.append(f"{index}\n{start} --> {end}\n{text}")

    return "\n\n".join(blocks).strip() + "\n"


def _render_vtt(rows: list[dict[str, Any]]) -> str:
    blocks = ["WEBVTT", ""]

    for row in rows:
        start = _subtitle_timestamp_vtt(row.get("start_sec"))
        end_value = row.get("end_sec")
        end = _subtitle_timestamp_vtt(end_value if end_value and end_value > row.get("start_sec", 0) else row.get("start_sec", 0) + 3)
        text = str(row.get("text") or "").strip()
        blocks.append(f"{start} --> {end}\n{text}")

    return "\n\n".join(blocks).strip() + "\n"


def _render_subtitle_txt(rows: list[dict[str, Any]]) -> str:
    lines: list[str] = []

    for row in rows:
        start = _subtitle_timestamp_vtt(row.get("start_sec"))
        end_value = row.get("end_sec")
        end = _subtitle_timestamp_vtt(end_value if end_value and end_value > row.get("start_sec", 0) else row.get("start_sec", 0) + 3)
        text = str(row.get("text") or "").strip()
        lines.append(f"[{start} - {end}] {text}")

    return "\n".join(lines).strip() + "\n"


def _subtitle_extension(format_name: str) -> str:
    return "txt" if format_name == "subtitle_txt" else format_name


def _subtitle_media_type(format_name: str) -> str:
    return {
        "txt": "text/plain; charset=utf-8",
        "subtitle_txt": "text/plain; charset=utf-8",
        "srt": "application/x-subrip",
        "vtt": "text/vtt",
        "json": "application/json",
    }.get((format_name or "").lower(), "application/octet-stream")


def _write_subtitle_file(path: Path, format_name: str, rows: list[dict[str, Any]], transcript: Transcript) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if format_name == "srt":
        content = _render_srt(rows)
        path.write_text(content, encoding="utf-8")
        return

    if format_name == "vtt":
        content = _render_vtt(rows)
        path.write_text(content, encoding="utf-8")
        return

    if format_name == "subtitle_txt":
        content = _render_subtitle_txt(rows)
        path.write_text(content, encoding="utf-8")
        return

    if format_name == "json":
        payload = {
            "transcript_id": transcript.id,
            "source_file_name": _source_file_name(transcript),
            "format": "subtitles_json",
            "segments": rows,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return

    raise ValueError(f"Unsupported subtitle format: {format_name}")


def _upsert_export_artifact(
    db: Session,
    *,
    transcript: Transcript,
    format_name: str,
    path: Path,
    overwrite: bool,
) -> ExportArtifact:
    existing = next(
        (
            artifact
            for artifact in transcript.export_artifacts
            if (artifact.format or "").lower() == format_name.lower()
        ),
        None,
    )

    relative_path = to_storage_relative_path(path)
    size_bytes = path.stat().st_size

    if existing is not None and overwrite:
        old_path = resolve_storage_path(existing.path)
        if old_path != path and old_path.exists() and old_path.is_file():
            old_path.unlink(missing_ok=True)

        existing.path = relative_path
        existing.size_bytes = size_bytes
        db.add(existing)
        return existing

    if existing is not None and not overwrite:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Subtitle artifact '{format_name}' already exists.",
        )

    artifact = ExportArtifact(
        transcript_id=transcript.id,
        format=format_name,
        path=relative_path,
        size_bytes=size_bytes,
    )
    db.add(artifact)
    return artifact


@router.get("", response_model=None, summary="List transcripts")
def list_transcripts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    stmt = (
        select(Transcript)
        .join(MediaAsset, Transcript.media_asset_id == MediaAsset.id)
        .options(
            selectinload(Transcript.media_asset),
            selectinload(Transcript.job),
            selectinload(Transcript.export_artifacts),
        )
        .where(MediaAsset.user_id == current_user.id)
        .order_by(Transcript.created_at.desc())
    )
    items = db.scalars(stmt).all()

    return [
        _build_transcript_response(item, include_segments=False, include_exports=True)
        for item in items
    ]


@router.post("/{transcript_id}/subtitles", response_model=None, summary="Generate subtitle files from transcript text")
def generate_subtitles(
    transcript_id: str,
    payload: SubtitleGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    transcript = _get_transcript_or_404(transcript_id, db, current_user)

    normalized_formats = []
    for item in payload.formats or []:
        normalized = str(item or "").strip().lower().replace("-", "_")
        if normalized == "txt":
            normalized = "subtitle_txt"
        if normalized in {"srt", "vtt", "subtitle_txt"} and normalized not in normalized_formats:
            normalized_formats.append(normalized)

    if not normalized_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Select at least one subtitle format: srt, vtt or txt.",
        )

    rows = _segment_rows(transcript)
    source_stem = _safe_stem(_source_file_name(transcript), transcript.id)
    output_dir = resolve_storage_path(Path("storage/transcripts/subtitles") / transcript.id)
    output_dir.mkdir(parents=True, exist_ok=True)

    artifacts: list[ExportArtifact] = []

    for format_name in normalized_formats:
        extension = _subtitle_extension(format_name)
        file_path = output_dir / f"{source_stem}.{extension}"
        _write_subtitle_file(file_path, format_name, rows, transcript)
        artifact = _upsert_export_artifact(
            db,
            transcript=transcript,
            format_name=format_name,
            path=file_path,
            overwrite=payload.overwrite,
        )
        artifacts.append(artifact)

    db.commit()

    stmt = (
        select(Transcript)
        .options(
            selectinload(Transcript.media_asset),
            selectinload(Transcript.job),
            selectinload(Transcript.segments),
            selectinload(Transcript.export_artifacts),
        )
        .where(Transcript.id == transcript.id)
    )
    refreshed = db.scalar(stmt) or transcript

    return {
        "status": "ok",
        "message": "Subtitle files generated.",
        "transcript": _build_transcript_response(refreshed),
        "artifacts": [_export_payload(artifact) for artifact in artifacts],
    }


@router.get("/export-artifacts/{artifact_id}/download", summary="Download transcript export artifact")
def download_export_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = _get_export_artifact_or_404(artifact_id, db, current_user)
    file_path = resolve_storage_path(item.path)

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export artifact file for '{artifact_id}' not found on disk",
        )

    media_type = _subtitle_media_type((item.format or "").lower())

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=file_path.name,
    )


@router.delete(
    "/export-artifacts/{artifact_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete transcript export artifact",
)
def delete_export_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    item = _get_export_artifact_or_404(artifact_id, db, current_user)
    file_path = resolve_storage_path(item.path)

    if file_path.exists() and file_path.is_file():
        file_path.unlink(missing_ok=True)

    db.delete(item)
    db.commit()

    sync_storage_usage_from_media_assets(db, current_user)

    return {"status": "ok", "message": f"Export artifact '{artifact_id}' deleted"}


@router.get("/{transcript_id}", response_model=None, summary="Get transcript by id")
def get_transcript(
    transcript_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    item = _get_transcript_or_404(transcript_id, db, current_user)
    return _build_transcript_response(item)


@router.delete(
    "/{transcript_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete transcript and its export files",
)
def delete_transcript(
    transcript_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    item = _get_transcript_or_404(transcript_id, db, current_user)

    for artifact in item.export_artifacts:
        artifact_path = resolve_storage_path(artifact.path)
        if artifact_path.exists() and artifact_path.is_file():
            artifact_path.unlink(missing_ok=True)

    db.delete(item)
    db.commit()

    sync_storage_usage_from_media_assets(db, current_user)

    return {"status": "ok", "message": f"Transcript '{transcript_id}' deleted"}
