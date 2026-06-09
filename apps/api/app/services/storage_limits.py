from __future__ import annotations

from pathlib import Path
from typing import Mapping

from fastapi import HTTPException, status


class FileSizeLimitExceeded(HTTPException):
    """Raised when an upload/download/export exceeds an application limit."""

    def __init__(self, *, label: str, size_bytes: int, limit_bytes: int) -> None:
        super().__init__(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=(
                f"{label} exceeds the configured size limit: "
                f"{size_bytes} bytes > {limit_bytes} bytes"
            ),
        )
        self.label = label
        self.size_bytes = size_bytes
        self.limit_bytes = limit_bytes


def assert_size_within_limit(size_bytes: int, limit_bytes: int, label: str) -> None:
    if int(size_bytes) > int(limit_bytes):
        raise FileSizeLimitExceeded(
            label=label,
            size_bytes=int(size_bytes),
            limit_bytes=int(limit_bytes),
        )


def assert_path_size_within_limit(path: Path, limit_bytes: int, label: str) -> int:
    size_bytes = path.stat().st_size
    assert_size_within_limit(size_bytes, limit_bytes, label)
    return size_bytes


def parse_content_length(headers: Mapping[str, str]) -> int | None:
    raw = headers.get("content-length") or headers.get("Content-Length")
    if raw is None or str(raw).strip() == "":
        return None

    try:
        value = int(str(raw).strip())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Content-Length header",
        ) from exc

    if value < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Content-Length header",
        )

    return value


def safe_unlink(path: Path | None) -> None:
    if path is None:
        return
    try:
        if path.exists() and path.is_file():
            path.unlink(missing_ok=True)
    except OSError:
        pass
