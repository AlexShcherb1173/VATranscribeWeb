import hashlib
import re
from pathlib import Path


def sanitize_file_name(name: str) -> str:
    name = name.strip()
    if not name:
        return "media"

    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()

    if len(name) > 120:
        name = name[:120].strip()

    return name or "media"


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()