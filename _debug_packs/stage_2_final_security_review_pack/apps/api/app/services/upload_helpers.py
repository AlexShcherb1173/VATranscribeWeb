import hashlib
import mimetypes
import uuid
from pathlib import Path

from fastapi import UploadFile

from apps.api.app.config import get_settings

settings = get_settings()

AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".avi",
}


def detect_kind(extension: str) -> str:
    ext = extension.lower()

    if ext in AUDIO_EXTENSIONS:
        return "audio"

    if ext in VIDEO_EXTENSIONS:
        return "video"

    raise ValueError(f"Unsupported file extension: {extension}")


def build_upload_dir(kind: str) -> Path:
    base = Path("storage/uploads")
    target = base / kind
    target.mkdir(parents=True, exist_ok=True)
    return target


def safe_file_name(name: str) -> str:
    cleaned = name.replace("\\", "_").replace("/", "_").strip()
    return cleaned or "file"


def generate_stored_name(original_name: str) -> str:
    ext = Path(original_name).suffix.lower()
    uid = uuid.uuid4().hex[:12]
    return f"{uid}{ext}"


async def save_upload_file(
    upload_file: UploadFile,
    target_path: Path,
) -> tuple[int, str]:
    sha256 = hashlib.sha256()
    total_size = 0

    with target_path.open("wb") as output:
        while True:
            chunk = await upload_file.read(1024 * 1024)
            if not chunk:
                break

            output.write(chunk)
            sha256.update(chunk)
            total_size += len(chunk)

    await upload_file.close()

    return total_size, sha256.hexdigest()


def guess_mime_type(path: Path) -> str | None:
    mime, _ = mimetypes.guess_type(str(path))
    return mime