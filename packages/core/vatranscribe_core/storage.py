from __future__ import annotations

from pathlib import Path

from apps.api.app.config import get_settings
from packages.core.vatranscribe_core.utils import sanitize_file_name


AUDIO_EXTENSIONS = {"mp3", "m4a", "aac", "wav", "flac", "ogg", "opus"}
VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "m4v", "mkv", "avi"}


def _download_base_dir(requested_format: str) -> Path:
    settings = get_settings()
    normalized_format = requested_format.lower().strip().lstrip(".")

    if normalized_format in AUDIO_EXTENSIONS:
        return getattr(settings, "downloads_audio_dir", settings.downloads_dir / "audio")

    return getattr(settings, "downloads_video_dir", settings.downloads_dir / "video")


def _normalize_requested_format(requested_format: str) -> str:
    normalized = requested_format.lower().strip().lstrip(".")

    if not normalized:
        raise ValueError("requested_format is required")

    if not normalized.replace("-", "").replace("_", "").isalnum():
        raise ValueError("requested_format contains invalid characters")

    return normalized


def build_download_target_path(requested_format: str, requested_file_name: str) -> Path:
    normalized_format = _normalize_requested_format(requested_format)

    safe_name = sanitize_file_name(requested_file_name).strip()
    if not safe_name:
        safe_name = "media_file"

    current_suffix = Path(safe_name).suffix.lower().lstrip(".")

    if current_suffix == normalized_format:
        final_name = safe_name
    else:
        safe_stem = Path(safe_name).stem if Path(safe_name).suffix else safe_name
        final_name = f"{safe_stem}.{normalized_format}"

    target_dir = _download_base_dir(normalized_format)
    target_dir.mkdir(parents=True, exist_ok=True)

    return target_dir / final_name


def get_project_root() -> Path:
    """Return project root inside container/local runtime.

    In Docker services the working directory is `/app`, so this resolves
    relative storage paths like `storage/downloads/video/file.mp4` to
    `/app/storage/downloads/video/file.mp4`.
    """
    settings = get_settings()
    storage_dir = Path(getattr(settings, "storage_dir", "storage"))

    if storage_dir.is_absolute():
        return storage_dir.parent

    # packages/core/vatranscribe_core/storage.py -> project root is parents[3]
    return Path(__file__).resolve().parents[3]


def resolve_storage_path(path: str | Path | None) -> Path:
    """Resolve DB/storage paths to an existing filesystem path when possible.

    DB rows intentionally store portable paths such as:
      storage/downloads/video/example.mp4

    Worker/API must use absolute runtime paths:
      /app/storage/downloads/video/example.mp4

    This function keeps absolute paths untouched and resolves relative paths
    against the current working directory and project root.
    """
    if path is None:
        raise ValueError("path is required")

    raw_path = Path(str(path).replace("\\", "/"))

    if raw_path.is_absolute():
        return raw_path

    candidates = [
        Path.cwd() / raw_path,
        get_project_root() / raw_path,
    ]

    settings = get_settings()
    storage_dir = Path(getattr(settings, "storage_dir", "storage"))

    if not storage_dir.is_absolute():
        candidates.append(get_project_root() / storage_dir / raw_path)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def to_storage_relative_path(path: str | Path) -> str:
    """Convert a filesystem path to a portable storage-relative DB path."""
    raw_path = Path(str(path).replace("\\", "/"))

    if not raw_path.is_absolute():
        return raw_path.as_posix()

    project_root = get_project_root()
    try:
        return raw_path.relative_to(project_root).as_posix()
    except ValueError:
        pass

    settings = get_settings()
    storage_dir = Path(getattr(settings, "storage_dir", "storage"))
    if storage_dir.is_absolute():
        try:
            return (Path("storage") / raw_path.relative_to(storage_dir)).as_posix()
        except ValueError:
            pass

    return raw_path.as_posix()
