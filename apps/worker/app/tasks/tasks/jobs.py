from __future__ import annotations

from datetime import datetime, timezone
import inspect
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from apps.api.app.config import get_settings
from apps.api.app.database import SessionLocal
from apps.api.app.models import (
    ExportArtifact,
    Job,
    JobLog,
    JobStatus,
    MediaAsset,
    Transcript,
    TranscriptSegment,
    User,
)
from apps.api.app.services.quota_service import (
    assert_can_store_bytes,
    increment_storage_used,
    increment_transcription_seconds_used,
)
from apps.worker.app.worker import celery
from packages.core.vatranscribe_core.audio_tools import extract_audio_for_transcription
from packages.core.vatranscribe_core.download_engine import download_media
from packages.core.vatranscribe_core.export_tools import write_json, write_srt, write_txt, write_vtt
from packages.core.vatranscribe_core.ffmpeg_tools import merge_video_and_audio_to_compatible_mp4
from packages.core.vatranscribe_core.media_probe import extract_basic_media_metadata
from packages.core.vatranscribe_core.storage import build_download_target_path, resolve_storage_path, to_storage_relative_path
from packages.core.vatranscribe_core.transcription_engine import transcribe_media
from packages.core.vatranscribe_core.utils import sha256_of_file


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def add_job_log(db: Session, job_id: str, level: str, message: str) -> None:
    now = _utcnow()

    db.add(JobLog(job_id=job_id, level=level, message=message))

    job = db.get(Job, job_id)
    if job is not None:
        if hasattr(job, "heartbeat_at"):
            job.heartbeat_at = now
        if hasattr(job, "last_log_at"):
            job.last_log_at = now
        if hasattr(job, "last_log_message"):
            job.last_log_message = message
        db.add(job)

    db.commit()


def update_job_progress(
    db: Session,
    job: Job,
    *,
    percent: int,
    stage: str | None = None,
    message: str | None = None,
    log: bool = False,
) -> None:
    safe_percent = max(0, min(100, int(percent)))
    now = _utcnow()

    if hasattr(job, "progress_percent"):
        job.progress_percent = safe_percent

    if hasattr(job, "progress_stage"):
        job.progress_stage = stage

    if hasattr(job, "progress_message"):
        job.progress_message = message

    if hasattr(job, "heartbeat_at"):
        job.heartbeat_at = now

    if message:
        if hasattr(job, "last_log_at"):
            job.last_log_at = now
        if hasattr(job, "last_log_message"):
            job.last_log_message = message

    db.add(job)
    db.commit()

    if log and message:
        add_job_log(db, job.id, "INFO", message)


def _download_progress_percent(event: dict[str, Any]) -> int | None:
    if event.get("status") == "finished":
        return 70

    if event.get("status") != "downloading":
        return None

    total = event.get("total_bytes") or event.get("total_bytes_estimate")
    downloaded = event.get("downloaded_bytes")

    if not total or not downloaded:
        return None

    raw_percent = int((float(downloaded) / float(total)) * 55)
    return max(10, min(70, 10 + raw_percent))


def _make_download_progress_hook(db: Session, job: Job):
    last_percent = {"value": -1}

    def hook(event: dict[str, Any]) -> None:
        percent = _download_progress_percent(event)
        if percent is None:
            return

        if percent == last_percent["value"]:
            return

        if percent - last_percent["value"] < 3 and percent not in {70}:
            return

        last_percent["value"] = percent
        update_job_progress(
            db,
            job,
            percent=percent,
            stage="download",
            message=f"Скачивание медиа: {percent}%",
            log=False,
        )

    return hook


def _transcription_progress_callback(db: Session, job: Job):
    last_percent = {"value": -1}

    def callback(event: dict[str, Any]) -> None:
        stage = str(event.get("stage") or "transcribe")

        if stage == "load_model":
            update_job_progress(
                db,
                job,
                percent=25,
                stage="load_model",
                message="Загрузка модели транскрибации",
                log=True,
            )
            return

        duration_sec = float(event.get("duration_sec") or 0)
        end_sec = float(event.get("end_sec") or 0)

        if duration_sec > 0:
            percent = 30 + int((end_sec / duration_sec) * 55)
        else:
            percent = min(85, 30 + int(event.get("index") or 0))

        percent = max(30, min(85, percent))

        if percent == last_percent["value"]:
            return

        if percent - last_percent["value"] < 3 and percent < 85:
            return

        last_percent["value"] = percent
        update_job_progress(
            db,
            job,
            percent=percent,
            stage="transcribe",
            message=f"Транскрибация: {percent}%",
            log=False,
        )

    return callback



def _guess_media_kind(requested_format: str) -> str:
    normalized = requested_format.lower().strip().lstrip(".")

    if normalized in {"mp3", "m4a", "aac", "wav", "flac", "ogg", "opus"}:
        return "audio"

    return "video"


def _guess_mime_type(requested_format: str) -> str:
    normalized = requested_format.lower().strip().lstrip(".")

    mime_types = {
        "mp3": "audio/mpeg",
        "m4a": "audio/mp4",
        "aac": "audio/aac",
        "wav": "audio/wav",
        "flac": "audio/flac",
        "ogg": "audio/ogg",
        "opus": "audio/opus",
        "mp4": "video/mp4",
        "webm": "video/webm",
        "mov": "video/quicktime",
        "m4v": "video/x-m4v",
        "mkv": "video/x-matroska",
        "avi": "video/x-msvideo",
        "txt": "text/plain",
        "srt": "application/x-subrip",
        "vtt": "text/vtt",
        "json": "application/json",
    }

    return mime_types.get(normalized, "application/octet-stream")


def _runtime_path(value: str | Path) -> Path:
    """Return a filesystem Path for settings/DB values.

    Some settings are Path objects, while others can arrive as strings.
    Export writers require Path because they call `path.parent`.
    """
    raw_path = Path(str(value).replace("\\", "/"))

    if raw_path.is_absolute():
        return raw_path

    return resolve_storage_path(raw_path)


def _ensure_directory_path(value: str | Path) -> Path:
    directory = _runtime_path(value)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _ensure_written_artifact(path: str | Path, *, artifact_format: str) -> Path:
    artifact_path = _runtime_path(path)

    if not artifact_path.exists() or not artifact_path.is_file():
        raise FileNotFoundError(
            f"Export artifact was not created: {artifact_format} "
            f"(path={path}, resolved={artifact_path}, cwd={Path.cwd()})"
        )

    if artifact_path.stat().st_size <= 0:
        raise FileNotFoundError(
            f"Export artifact is empty: {artifact_format} "
            f"(path={path}, resolved={artifact_path}, cwd={Path.cwd()})"
        )

    return artifact_path


def _run_command(command: list[str], *, job_id: str | None = None, db: Session | None = None) -> subprocess.CompletedProcess[str]:
    if db is not None and job_id is not None:
        add_job_log(db, job_id, "INFO", "Running command: " + " ".join(command))

    completed = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    output = (completed.stdout or "").strip()

    if output and db is not None and job_id is not None:
        tail = "\n".join(output.splitlines()[-20:])
        add_job_log(db, job_id, "INFO", f"Command output tail:\n{tail}")

    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {completed.returncode}: {' '.join(command)}\n{output}"
        )

    return completed


def _normalize_audio_for_whisper(*, input_path: Path, output_path: Path, db: Session, job: Job) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=11",
        str(output_path),
    ]

    try:
        _run_command(command, job_id=job.id, db=db)
    except Exception as exc:
        add_job_log(
            db,
            job.id,
            "WARNING",
            f"Audio normalization failed, using unnormalized audio: {exc}",
        )
        shutil.copyfile(input_path, output_path)

    return output_path


def _find_demucs_vocals_file(output_dir: Path, source_stem: str) -> Path | None:
    expected = output_dir / "htdemucs" / source_stem / "vocals.wav"

    if expected.exists() and expected.is_file():
        return expected

    matches = sorted(output_dir.glob("**/vocals.wav"))
    return matches[0] if matches else None


def _isolate_vocals_with_demucs(*, audio_path: Path, temp_dir: Path, db: Session, job: Job) -> Path:
    demucs_output_dir = temp_dir / f"{job.id}_demucs"

    if demucs_output_dir.exists():
        shutil.rmtree(demucs_output_dir, ignore_errors=True)

    demucs_output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        "python",
        "-m",
        "demucs",
        "--two-stems=vocals",
        "--device",
        "cpu",
        "-n",
        "htdemucs",
        "--out",
        str(demucs_output_dir),
        str(audio_path),
    ]

    try:
        _run_command(command, job_id=job.id, db=db)
    except Exception as first_exc:
        add_job_log(
            db,
            job.id,
            "WARNING",
            "python -m demucs failed, trying demucs executable. "
            "If both fail, install demucs/torch/torchaudio in the worker image.",
        )
        command = [
            "demucs",
            "--two-stems=vocals",
            "--device",
            "cpu",
            "-n",
            "htdemucs",
            "--out",
            str(demucs_output_dir),
            str(audio_path),
        ]

        try:
            _run_command(command, job_id=job.id, db=db)
        except Exception as second_exc:
            raise RuntimeError(
                "Lyrics / Music clip requires Demucs in the worker container. "
                "Install Python packages: demucs torch torchaudio. "
                f"First error: {first_exc}. Second error: {second_exc}"
            ) from second_exc

    vocals_path = _find_demucs_vocals_file(demucs_output_dir, audio_path.stem)

    if vocals_path is None:
        raise FileNotFoundError(
            f"Demucs did not create vocals.wav in {demucs_output_dir}"
        )

    add_job_log(db, job.id, "INFO", f"Demucs vocals extracted: {vocals_path}")

    normalized_vocals_path = temp_dir / f"{job.id}_vocals_normalized.wav"
    return _normalize_audio_for_whisper(
        input_path=vocals_path,
        output_path=normalized_vocals_path,
        db=db,
        job=job,
    )


def _segment_duration(segment: dict[str, Any]) -> float:
    start = float(segment.get("start_sec") or segment.get("start") or 0.0)
    end = float(segment.get("end_sec") or segment.get("end") or 0.0)
    return max(0.0, end - start)


def _transcript_quality_metrics(*, full_text: str, segments: list[dict[str, Any]], duration_sec: int) -> dict[str, Any]:
    text_length = len((full_text or "").strip())
    segment_count = len(segments or [])
    coverage_sec_float = sum(_segment_duration(segment) for segment in segments or [])
    coverage_sec = int(round(coverage_sec_float))
    coverage_ratio = coverage_sec_float / float(duration_sec) if duration_sec > 0 else 0.0

    if text_length == 0 or segment_count == 0:
        quality_status = "empty"
        quality_warning = (
            "Transcript is empty: the model did not find recognizable speech. "
            "For music videos, use Lyrics / Music clip with vocal isolation."
        )
    elif duration_sec >= 180 and (coverage_ratio < 0.08 or text_length < 250):
        quality_status = "low_quality"
        quality_warning = (
            "Transcript quality is low for the media duration. "
            "The audio likely contains music, noise, chorus, applause or overlapping vocals. "
            "Use Lyrics / Music clip or try a larger model."
        )
    elif duration_sec >= 60 and (coverage_ratio < 0.18 or text_length < 100):
        quality_status = "partial"
        quality_warning = (
            "Transcript looks partial for the media duration. "
            "Review it before using subtitles or content generation."
        )
    else:
        quality_status = "good"
        quality_warning = None

    return {
        "segments_count": segment_count,
        "text_length": text_length,
        "coverage_sec": coverage_sec,
        "coverage_ratio": coverage_ratio,
        "quality_status": quality_status,
        "quality_warning": quality_warning,
    }


def _safe_export_stem(value: str | None, fallback: str) -> str:
    """Build a readable, filesystem-safe export basename.

    The source media filename is preferred, while UUID is used only as a fallback.
    Cyrillic, Latin letters, digits, spaces, dots, hyphens and underscores are preserved.
    """
    raw = (value or fallback or "transcript").strip()
    stem = Path(raw).stem.strip()

    stem = re.sub(r"[^\w\s.\-]+", "_", stem, flags=re.UNICODE)
    stem = re.sub(r"\s+", "_", stem, flags=re.UNICODE)
    stem = re.sub(r"_+", "_", stem, flags=re.UNICODE)
    stem = stem.strip("._- ")

    if not stem:
        stem = fallback or "transcript"

    return stem[:140]


def _export_stem_for_transcript(media_asset: MediaAsset, transcript: Transcript) -> str:
    return _safe_export_stem(
        media_asset.original_name or media_asset.stored_name or media_asset.path,
        transcript.id,
    )


def _unique_export_stem(
    directories: list[Path],
    preferred_stem: str,
    extensions: list[str],
) -> str:
    """Return one basename that is free for all export formats.

    This keeps TXT/SRT/VTT/JSON filenames consistent:
    `source.txt`, `source.srt`, ...
    or `source_1.txt`, `source_1.srt`, ...
    """
    safe_stem = _safe_export_stem(preferred_stem, "transcript")
    normalized_extensions = [extension.lower().lstrip(".") for extension in extensions]

    index = 0

    while True:
        suffix = "" if index == 0 else f"_{index}"
        candidate_stem = f"{safe_stem}{suffix}"

        has_collision = any(
            (directory / f"{candidate_stem}.{extension}").exists()
            for directory in directories
            for extension in normalized_extensions
        )

        if not has_collision:
            return candidate_stem

        index += 1


def _remove_file_safely(path: Path) -> None:
    try:
        if path.exists() and path.is_file():
            path.unlink(missing_ok=True)
    except OSError:
        pass


def _duration_from_segments(segments: list[dict[str, Any]]) -> int:
    if not segments:
        return 0

    last_end = max(int(segment.get("end_sec") or 0) for segment in segments)
    return max(last_end, 0)




def _normalize_transcription_language(value: str | None) -> str | None:
    """Return None for automatic language detection.

    faster-whisper treats language=None as auto-detect. The UI sends
    "auto" by default, while older jobs may have NULL/empty values.
    """
    if value is None:
        return None

    normalized = str(value).strip().lower()

    if normalized in {"", "auto", "detect", "auto-detect", "autodetect", "none", "null"}:
        return None

    return normalized




def _normalize_transcription_profile(value: str | None) -> str:
    normalized = (value or "speech").strip().lower().replace("-", "_").replace(" ", "_")

    aliases = {
        "standard": "speech",
        "fast": "speech",
        "accurate": "speech",
        "content": "speech",
        "content_pack": "speech",
        "default": "speech",
        "meeting": "speech",
        "lecture": "speech",
        "music": "music_vocal",
        "song": "music_vocal",
        "vocal": "music_vocal",
        "music_vocal": "music_vocal",
        "music_and_vocal": "music_vocal",
        "lyrics": "lyrics_music",
        "lyric": "lyrics_music",
        "lyrics_music": "lyrics_music",
        "music_clip": "lyrics_music",
        "clip": "lyrics_music",
        "karaoke": "lyrics_music",
        "song_lyrics": "lyrics_music",
        "noisy": "noisy_speech",
        "noisy_speech": "noisy_speech",
    }

    return aliases.get(
        normalized,
        normalized if normalized in {"speech", "music_vocal", "lyrics_music", "noisy_speech"} else "speech",
    )


def _transcription_engine_options(profile: str) -> dict[str, Any]:
    """Return profile-specific options for the core transcription engine.

    The core function may not support every option in older local builds.
    `_call_transcribe_media` filters unsupported kwargs at runtime.
    """

    if profile == "lyrics_music":
        return {
            "vad_filter": False,
            "condition_on_previous_text": True,
            "beam_size": 5,
            "temperature": 0,
            "no_speech_threshold": 0.95,
            "log_prob_threshold": -1.4,
            "compression_ratio_threshold": 3.0,
        }

    if profile == "music_vocal":
        return {
            "vad_filter": False,
            "condition_on_previous_text": True,
            "beam_size": 5,
            "temperature": 0,
            "no_speech_threshold": 0.9,
            "log_prob_threshold": -1.2,
            "compression_ratio_threshold": 2.8,
        }

    if profile == "noisy_speech":
        return {
            "vad_filter": True,
            "vad_parameters": {
                "min_silence_duration_ms": 900,
                "speech_pad_ms": 600,
            },
            "condition_on_previous_text": True,
            "beam_size": 5,
            "temperature": 0,
            "no_speech_threshold": 0.75,
        }

    return {
        "vad_filter": True,
        "condition_on_previous_text": False,
        "beam_size": 5,
        "temperature": 0,
    }


def _call_transcribe_media(
    *,
    audio_path: Path,
    model_name: str,
    language: str | None,
    profile: str,
    progress_callback,
) -> dict[str, Any]:
    options = _transcription_engine_options(profile)
    base_kwargs: dict[str, Any] = {
        "audio_path": audio_path,
        "model_name": model_name,
        "language": language,
        "progress_callback": progress_callback,
        **options,
    }

    try:
        signature = inspect.signature(transcribe_media)
        accepted_kwargs = {
            key: value
            for key, value in base_kwargs.items()
            if key in signature.parameters
        }
        return transcribe_media(**accepted_kwargs)
    except TypeError:
        # Backward compatibility with older core signature:
        # transcribe_media(*, audio_path, model_name, language=None, progress_callback=None)
        return transcribe_media(
            audio_path=audio_path,
            model_name=model_name,
            language=language,
            progress_callback=progress_callback,
        )





def _transcribe_with_faster_whisper_direct(
    *,
    audio_path: Path,
    model_name: str,
    language: str | None,
    profile: str,
) -> dict[str, Any]:
    """Direct fallback for audio profiles that need precise Whisper options.

    This is used when the shared core engine returns an empty result. It avoids
    VAD for music/vocal material where voice activity detection often removes
    singing as background music/noise.
    """

    from faster_whisper import WhisperModel

    options = _transcription_engine_options(profile)
    vad_filter = bool(options.get("vad_filter", True))

    model = WhisperModel(model_name, device="cpu", compute_type="int8")

    segments_iter, info = model.transcribe(
        str(audio_path),
        language=language,
        vad_filter=vad_filter,
        beam_size=int(options.get("beam_size", 5)),
        condition_on_previous_text=bool(options.get("condition_on_previous_text", False)),
        temperature=options.get("temperature", 0),
        no_speech_threshold=float(options.get("no_speech_threshold", 0.6)),
        log_prob_threshold=float(options.get("log_prob_threshold", -1.0)),
        compression_ratio_threshold=float(options.get("compression_ratio_threshold", 2.4)),
    )

    segments: list[dict[str, Any]] = []

    for item in segments_iter:
        text = (getattr(item, "text", "") or "").strip()

        if not text:
            continue

        segments.append(
            {
                "start_sec": float(getattr(item, "start", 0.0) or 0.0),
                "end_sec": float(getattr(item, "end", 0.0) or 0.0),
                "text": text,
            }
        )

    full_text = " ".join(segment["text"] for segment in segments).strip()

    return {
        "engine": "faster-whisper",
        "language": getattr(info, "language", None) or language,
        "duration_sec": int(float(getattr(info, "duration", 0.0) or 0.0)),
        "text": full_text,
        "full_text": full_text,
        "segments": segments,
    }


def _transcript_result_is_empty(result: dict[str, Any]) -> bool:
    full_text = (result.get("text") or result.get("full_text") or "").strip()
    segments = result.get("segments") or []

    return not full_text and not segments


def _is_transcript_suspiciously_short(*, full_text: str, segments: list[dict[str, Any]], duration_sec: int) -> bool:
    text_length = len((full_text or "").strip())
    segment_count = len(segments or [])

    if duration_sec >= 60 and text_length < 100:
        return True

    if duration_sec >= 300 and segment_count < 3:
        return True

    return False

def _model_columns(model: type) -> set[str]:
    return set(model.__table__.columns.keys())


def _filtered_model_kwargs(model: type, values: dict[str, Any]) -> dict[str, Any]:
    columns = _model_columns(model)
    return {key: value for key, value in values.items() if key in columns}


def _add_model_instance(db: Session, model: type, values: dict[str, Any]) -> Any:
    instance = model(**_filtered_model_kwargs(model, values))
    db.add(instance)
    return instance



def _normalize_download_engine_mode(job: Job) -> str:
    raw_mode = (job.mp4_mode or "video_mp4_compatible").lower().strip()

    if raw_mode in {
        "audio_mp3",
        "video_mp4_compatible",
        "video_mp4_fast",
        "selected_original",
        "best_available",
    }:
        return raw_mode

    if raw_mode in {"compatible", "fast"}:
        return raw_mode

    return "video_mp4_compatible"


def _run_download_job(db: Session, job: Job) -> dict[str, Any]:
    if not job.input_url:
        raise ValueError("Download job requires input_url")

    if not job.requested_format:
        raise ValueError("Download job requires requested_format")

    if not job.requested_file_name:
        raise ValueError("Download job requires requested_file_name")

    requested_format = job.requested_format.lower().strip().lstrip(".")
    download_mode = _normalize_download_engine_mode(job)

    update_job_progress(
        db,
        job,
        percent=5,
        stage="prepare",
        message="Подготовка скачивания",
        log=True,
    )

    add_job_log(db, job.id, "INFO", f"Preparing download for URL: {job.input_url}")
    add_job_log(db, job.id, "INFO", f"Download mode: {download_mode}")
    add_job_log(db, job.id, "INFO", f"Requested format: {requested_format}")
    add_job_log(db, job.id, "INFO", f"Requested file name: {job.requested_file_name}")

    target_path = build_download_target_path(
        requested_format=requested_format,
        requested_file_name=job.requested_file_name,
    )

    add_job_log(db, job.id, "INFO", f"Target path: {target_path}")

    result = download_media(
        url=job.input_url,
        requested_format=requested_format,
        output_path=target_path,
        mp4_mode=download_mode,
        video_format_id=job.selected_video_format_id,
        audio_format_id=job.selected_audio_format_id,
        progress_hook=_make_download_progress_hook(db, job),
    )

    if requested_format == "mp4" and result.get("mp4_mode") == "compatible":
        video_path = resolve_storage_path(result["video_path"])
        audio_path = resolve_storage_path(result["audio_path"])
        final_path = resolve_storage_path(result["final_path"])

        add_job_log(db, job.id, "INFO", f"Downloaded video stream: {video_path}")
        add_job_log(db, job.id, "INFO", f"Downloaded audio stream: {audio_path}")
        update_job_progress(
            db,
            job,
            percent=78,
            stage="merge",
            message="Объединение видео и аудио",
            log=True,
        )

        add_job_log(db, job.id, "INFO", "Running ffmpeg compatible merge: video copy + audio AAC")

        final_path = merge_video_and_audio_to_compatible_mp4(
            video_path=video_path,
            audio_path=audio_path,
            output_path=final_path,
        )

        _remove_file_safely(video_path)
        _remove_file_safely(audio_path)

        add_job_log(db, job.id, "INFO", f"Compatible MP4 created: {final_path}")
    else:
        final_path = resolve_storage_path(result["final_path"])
        add_job_log(db, job.id, "INFO", f"Download completed: {final_path}")

    update_job_progress(
        db,
        job,
        percent=92,
        stage="storage",
        message="Создание записи медиафайла",
        log=True,
    )

    final_extension = final_path.suffix.lower().lstrip(".") or requested_format
    metadata = extract_basic_media_metadata(final_path)
    size_bytes = int(metadata.get("size_bytes") or 0)

    user = db.get(User, job.user_id) if job.user_id else None

    if user is not None:
        try:
            assert_can_store_bytes(db, user, size_bytes)
        except Exception:
            _remove_file_safely(final_path)
            raise

    checksum = sha256_of_file(final_path)

    media_asset = MediaAsset(
        user_id=job.user_id,
        kind=_guess_media_kind(final_extension),
        original_name=final_path.name,
        stored_name=final_path.name,
        mime_type=_guess_mime_type(final_extension),
        extension=final_extension,
        size_bytes=size_bytes,
        duration_sec=metadata.get("duration_sec"),
        path=to_storage_relative_path(final_path),
        checksum_sha256=checksum,
    )

    db.add(media_asset)
    db.commit()
    db.refresh(media_asset)

    if user is not None:
        increment_storage_used(db, user, size_bytes)

    add_job_log(db, job.id, "INFO", f"Media asset created: {media_asset.id}")

    if metadata.get("video_codec"):
        add_job_log(db, job.id, "INFO", f"Video codec: {metadata['video_codec']}")

    if metadata.get("audio_codec"):
        add_job_log(db, job.id, "INFO", f"Audio codec: {metadata['audio_codec']}")

    job.output_media_asset_id = media_asset.id
    db.add(job)
    db.commit()

    update_job_progress(
        db,
        job,
        percent=100,
        stage="done",
        message="Скачивание завершено",
        log=True,
    )

    return {
        "output_media_asset_id": media_asset.id,
        "path": to_storage_relative_path(final_path),
        "size_bytes": media_asset.size_bytes or 0,
    }


def _run_transcription_job(db: Session, job: Job) -> dict[str, Any]:
    if not job.transcription_media_asset_id:
        raise ValueError("Transcription job requires transcription_media_asset_id")

    media_asset = db.get(MediaAsset, job.transcription_media_asset_id)

    if media_asset is None:
        raise ValueError(f"Media asset not found: {job.transcription_media_asset_id}")

    settings = get_settings()
    source_path = resolve_storage_path(media_asset.path)

    add_job_log(db, job.id, "INFO", f"Stored media path: {media_asset.path}")
    add_job_log(db, job.id, "INFO", f"Resolved media path: {source_path}")

    if not source_path.exists() or not source_path.is_file():
        raise FileNotFoundError(
            f"Media file not found: {media_asset.path} "
            f"(resolved to {source_path}, cwd={Path.cwd()})"
        )

    model_name = (
        job.transcription_model
        or getattr(settings, "default_transcription_model", None)
        or "medium"
    )

    language = _normalize_transcription_language(job.transcription_language)
    transcription_profile = _normalize_transcription_profile(
        getattr(job, "transcription_profile", None)
    )
    if transcription_profile == "lyrics_music" and str(model_name).lower() in {"tiny", "base", "small"}:
        add_job_log(
            db,
            job.id,
            "INFO",
            f"Lyrics / Music clip requires a stronger model. Upgrading model {model_name} -> medium.",
        )
        model_name = "medium"

    transcription_options = _transcription_engine_options(transcription_profile)

    update_job_progress(
        db,
        job,
        percent=5,
        stage="prepare",
        message="Подготовка транскрибации",
        log=True,
    )

    add_job_log(db, job.id, "INFO", f"Preparing transcription for media asset: {media_asset.id}")
    add_job_log(db, job.id, "INFO", f"Source path: {source_path}")
    add_job_log(db, job.id, "INFO", f"Model: {model_name}")
    add_job_log(db, job.id, "INFO", f"Language mode: {language or 'auto-detect'}")
    add_job_log(db, job.id, "INFO", f"Audio profile: {transcription_profile}")
    add_job_log(
        db,
        job.id,
        "INFO",
        "Whisper params: "
        + ", ".join(f"{key}={value}" for key, value in transcription_options.items()),
    )

    temp_dir = _ensure_directory_path(settings.temp_dir)
    audio_path = temp_dir / f"{job.id}_transcription.wav"

    update_job_progress(
        db,
        job,
        percent=15,
        stage="extract_audio",
        message="Извлечение аудио",
        log=True,
    )

    audio_path = extract_audio_for_transcription(
        input_path=source_path,
        output_path=audio_path,
    )

    add_job_log(db, job.id, "INFO", f"Audio prepared: {audio_path}")

    transcription_audio_path = audio_path
    isolated_vocals_path: Path | None = None

    if transcription_profile == "lyrics_music":
        update_job_progress(
            db,
            job,
            percent=22,
            stage="vocal_isolation",
            message="Отделение вокала от музыки",
            log=True,
        )
        isolated_vocals_path = _isolate_vocals_with_demucs(
            audio_path=audio_path,
            temp_dir=temp_dir,
            db=db,
            job=job,
        )
        transcription_audio_path = isolated_vocals_path
        add_job_log(db, job.id, "INFO", f"Using isolated vocals for transcription: {transcription_audio_path}")

    result = _call_transcribe_media(
        audio_path=transcription_audio_path,
        model_name=model_name,
        language=language,
        profile=transcription_profile,
        progress_callback=_transcription_progress_callback(db, job),
    )

    if _transcript_result_is_empty(result) and transcription_profile in {"music_vocal", "lyrics_music", "noisy_speech"}:
        add_job_log(
            db,
            job.id,
            "WARNING",
            "Первый проход вернул 0 сегментов. Запускаем fallback faster-whisper "
            f"для профиля {transcription_profile}.",
        )
        result = _transcribe_with_faster_whisper_direct(
            audio_path=transcription_audio_path,
            model_name=model_name,
            language=language,
            profile=transcription_profile,
        )

    full_text = result.get("text") or result.get("full_text") or ""
    segments = result.get("segments") or []
    duration_sec = int(
        result.get("duration_sec")
        or media_asset.duration_sec
        or _duration_from_segments(segments)
        or 0
    )
    detected_language = result.get("language") or language or "auto"

    quality = _transcript_quality_metrics(
        full_text=full_text,
        segments=segments,
        duration_sec=duration_sec,
    )

    add_job_log(db, job.id, "INFO", f"Detected language: {detected_language}")
    add_job_log(db, job.id, "INFO", f"Segments created: {len(segments)}")
    add_job_log(db, job.id, "INFO", f"Full text length: {len(full_text.strip())}")
    add_job_log(db, job.id, "INFO", f"Coverage ratio: {quality['coverage_ratio']:.3f}")
    add_job_log(db, job.id, "INFO", f"Quality status: {quality['quality_status']}")

    transcript_is_empty = not full_text.strip() and not segments

    if transcript_is_empty:
        failed_message = (
            "Транскрипт пустой: модель не нашла распознаваемую речь. "
            "Для музыкальных клипов и вокала повторите задачу с профилем "
            "«Клип / текст песни» / Lyrics / Music clip. Для шумного аудио используйте "
            "профиль «Шумная речь» / Noisy speech."
        )
        add_job_log(db, job.id, "ERROR", failed_message)
        raise ValueError(failed_message)

    if _is_transcript_suspiciously_short(
        full_text=full_text,
        segments=segments,
        duration_sec=duration_sec,
    ):
        warning_message = (
            "Транскрипт слишком короткий для длительности файла. "
            "Возможные причины: неверно выбран язык, в файле музыка/шум, "
            "VAD отфильтровал речь или модель не смогла распознать аудио. "
            "Попробуйте повторить транскрибацию с языком Auto, English, "
            "Lyrics / Music clip, Music & vocal или Noisy speech."
        )
        add_job_log(db, job.id, "WARNING", warning_message)
        if hasattr(job, "progress_message"):
            job.progress_message = warning_message
        if hasattr(job, "last_log_message"):
            job.last_log_message = warning_message
        db.add(job)
        db.commit()

    if quality.get("quality_warning"):
        add_job_log(db, job.id, "WARNING", str(quality["quality_warning"]))

    update_job_progress(
        db,
        job,
        percent=88,
        stage="save_transcript",
        message="Сохранение транскрипта",
        log=True,
    )

    transcript = _add_model_instance(
        db,
        Transcript,
        {
            "job_id": job.id,
            "media_asset_id": media_asset.id,
            "engine": result.get("engine") or "faster-whisper",
            "model_name": model_name,
            "language": detected_language if detected_language != "auto" else None,
            "full_text": full_text,
            "duration_sec": duration_sec,
            "segments_count": quality["segments_count"],
            "coverage_sec": quality["coverage_sec"],
            "coverage_ratio": f"{quality['coverage_ratio']:.6f}",
            "quality_status": quality["quality_status"],
            "quality_warning": quality["quality_warning"],
        },
    )
    db.commit()
    db.refresh(transcript)

    add_job_log(db, job.id, "INFO", f"Transcript created: {transcript.id}")

    if isolated_vocals_path is not None and isolated_vocals_path.exists():
        vocals_dir = _ensure_directory_path(settings.transcripts_txt_dir).parent / "vocals"
        vocals_dir.mkdir(parents=True, exist_ok=True)
        vocals_stem = _safe_export_stem(
            media_asset.original_name or media_asset.stored_name or media_asset.path,
            transcript.id,
        )
        vocals_target = vocals_dir / f"{vocals_stem}_{job.id[:8]}_vocals.wav"
        shutil.copyfile(isolated_vocals_path, vocals_target)
        _add_model_instance(
            db,
            ExportArtifact,
            {
                "user_id": job.user_id,
                "transcript_id": transcript.id,
                "format": "vocals_wav",
                "path": to_storage_relative_path(vocals_target),
                "size_bytes": vocals_target.stat().st_size,
            },
        )
        db.commit()
        add_job_log(db, job.id, "INFO", f"Isolated vocals artifact created: {vocals_target}")

    for index, segment in enumerate(segments):
        _add_model_instance(
            db,
            TranscriptSegment,
            {
                "transcript_id": transcript.id,
                "position": index,
                "order_index": index,
                "start_sec": float(segment.get("start_sec") or segment.get("start") or 0),
                "end_sec": float(segment.get("end_sec") or segment.get("end") or 0),
                "text": segment.get("text") or "",
            },
        )

    db.commit()

    txt_dir = _ensure_directory_path(settings.transcripts_txt_dir)
    srt_dir = _ensure_directory_path(settings.transcripts_srt_dir)
    vtt_dir = _ensure_directory_path(settings.transcripts_vtt_dir)
    json_dir = _ensure_directory_path(settings.transcripts_json_dir)

    export_stem = _unique_export_stem(
        directories=[txt_dir, srt_dir, vtt_dir, json_dir],
        preferred_stem=_export_stem_for_transcript(media_asset, transcript),
        extensions=["txt", "srt", "vtt", "json"],
    )

    txt_path = txt_dir / f"{export_stem}.txt"
    srt_path = srt_dir / f"{export_stem}.srt"
    vtt_path = vtt_dir / f"{export_stem}.vtt"
    json_path = json_dir / f"{export_stem}.json"

    update_job_progress(
        db,
        job,
        percent=93,
        stage="export",
        message="Экспорт TXT/SRT/VTT/JSON",
        log=True,
    )

    txt_path = _runtime_path(txt_path)
    srt_path = _runtime_path(srt_path)
    vtt_path = _runtime_path(vtt_path)
    json_path = _runtime_path(json_path)

    txt_path.parent.mkdir(parents=True, exist_ok=True)
    srt_path.parent.mkdir(parents=True, exist_ok=True)
    vtt_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    written_artifacts = [
        ("txt", txt_path, write_txt(txt_path, full_text)),
        ("srt", srt_path, write_srt(srt_path, segments)),
        ("vtt", vtt_path, write_vtt(vtt_path, segments)),
        (
            "json",
            json_path,
            write_json(
                json_path,
                {
                    "id": transcript.id,
                    "media_asset_id": media_asset.id,
                    "engine": transcript.engine,
                    "model_name": transcript.model_name,
                    "language": transcript.language,
                    "detected_language": detected_language,
                    "duration_sec": duration_sec,
                    "full_text": transcript.full_text,
                    "segments": segments,
                    "quality": {
                        "status": quality["quality_status"],
                        "warning": quality["quality_warning"],
                        "segments_count": quality["segments_count"],
                        "text_length": quality["text_length"],
                        "coverage_sec": quality["coverage_sec"],
                        "coverage_ratio": quality["coverage_ratio"],
                    },
                    "audio_profile": transcription_profile,
                },
            ),
        ),
    ]

    for artifact_format, expected_path, returned_path in written_artifacts:
        artifact_path = _ensure_written_artifact(
            returned_path or expected_path,
            artifact_format=artifact_format,
        )
        artifact_size = artifact_path.stat().st_size

        _add_model_instance(
            db,
            ExportArtifact,
            {
                "user_id": job.user_id,
                "transcript_id": transcript.id,
                "format": artifact_format,
                "path": to_storage_relative_path(artifact_path),
                "size_bytes": artifact_size,
            },
        )

    db.commit()

    user = db.get(User, job.user_id) if job.user_id else None

    if user is not None and duration_sec > 0:
        increment_transcription_seconds_used(db, user, duration_sec)

    if hasattr(job, "transcript_id"):
        job.transcript_id = transcript.id

    db.add(job)
    db.commit()

    update_job_progress(
        db,
        job,
        percent=100,
        stage="done",
        message="Транскрибация завершена",
        log=True,
    )

    return {
        "transcript_id": transcript.id,
        "media_asset_id": media_asset.id,
        "duration_sec": duration_sec,
        "segments_count": len(segments),
        "quality_status": quality["quality_status"],
        "coverage_ratio": quality["coverage_ratio"],
    }


@celery.task(name="vatranscribe.jobs.execute")
def execute_job_task(job_id: str) -> None:
    db = SessionLocal()
    job: Job | None = None

    try:
        job = db.get(Job, job_id)

        if job is None:
            return

        now = _utcnow()
        job.status = JobStatus.RUNNING.value
        job.started_at = now
        job.finished_at = None
        job.error_message = None
        if hasattr(job, "progress_percent"):
            job.progress_percent = 0
        if hasattr(job, "progress_stage"):
            job.progress_stage = "queued"
        if hasattr(job, "progress_message"):
            job.progress_message = "Задача запущена"
        if hasattr(job, "heartbeat_at"):
            job.heartbeat_at = now
        if hasattr(job, "last_log_at"):
            job.last_log_at = now
        if hasattr(job, "last_log_message"):
            job.last_log_message = "Задача запущена"
        db.add(job)
        db.commit()
        db.refresh(job)

        add_job_log(db, job.id, "INFO", "Job started")

        if job.type == "download":
            result = _run_download_job(db, job)
            add_job_log(db, job.id, "INFO", f"Download result: {result}")
        elif job.type in {"transcribe", "transcription"}:
            result = _run_transcription_job(db, job)
            add_job_log(db, job.id, "INFO", f"Transcription result: {result}")
        else:
            raise ValueError(f"Unsupported job type: {job.type}")

        now = _utcnow()
        job.status = JobStatus.SUCCEEDED.value
        job.finished_at = now
        if hasattr(job, "progress_percent"):
            job.progress_percent = 100
        if hasattr(job, "progress_stage"):
            job.progress_stage = "done"
        if hasattr(job, "progress_message"):
            job.progress_message = "Готово"
        if hasattr(job, "heartbeat_at"):
            job.heartbeat_at = now
        if hasattr(job, "last_log_at"):
            job.last_log_at = now
        if hasattr(job, "last_log_message"):
            job.last_log_message = "Готово"
        db.add(job)
        db.commit()

        add_job_log(db, job.id, "INFO", "Job finished successfully")

    except Exception as exc:
        if job is not None:
            now = _utcnow()
            job.status = JobStatus.FAILED.value
            job.finished_at = now
            job.error_message = str(exc)
            if hasattr(job, "progress_stage"):
                job.progress_stage = "failed"
            if hasattr(job, "progress_message"):
                job.progress_message = str(exc)
            if hasattr(job, "heartbeat_at"):
                job.heartbeat_at = now
            if hasattr(job, "last_log_at"):
                job.last_log_at = now
            if hasattr(job, "last_log_message"):
                job.last_log_message = str(exc)
            db.add(job)
            db.commit()

            add_job_log(db, job.id, "ERROR", f"Job failed: {exc}")

        raise

    finally:
        db.close()
