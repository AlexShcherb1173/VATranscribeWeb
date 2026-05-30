from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from apps.api.app.config import get_settings
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import User

router = APIRouter(prefix="/settings", tags=["settings"])


class YoutubeCookiesStatusResponse(BaseModel):
    configured: bool
    exists: bool
    path: str | None
    size_bytes: int | None


def _cookies_target_path() -> Path:
    settings = get_settings()

    if settings.yt_dlp_cookies_file:
        return settings.yt_dlp_cookies_file

    return settings.cookies_dir / "youtube.txt"


def _validate_cookies_file(content: bytes) -> None:
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cookies file is empty",
        )

    text = content.decode("utf-8", errors="ignore")

    if "# Netscape HTTP Cookie File" not in text and ".youtube.com" not in text and "youtube.com" not in text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid cookies.txt file. Export cookies for youtube.com in Netscape cookies.txt format.",
        )


@router.get("/youtube-cookies", response_model=YoutubeCookiesStatusResponse)
def get_youtube_cookies_status(
    current_user: User = Depends(get_current_user),
) -> YoutubeCookiesStatusResponse:
    target_path = _cookies_target_path()
    exists = target_path.exists() and target_path.is_file()

    return YoutubeCookiesStatusResponse(
        configured=True,
        exists=exists,
        path=str(target_path).replace("\\", "/"),
        size_bytes=target_path.stat().st_size if exists else None,
    )


@router.post("/youtube-cookies", response_model=YoutubeCookiesStatusResponse)
async def upload_youtube_cookies(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> YoutubeCookiesStatusResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cookies file is required",
        )

    content = await file.read()
    _validate_cookies_file(content)

    target_path = _cookies_target_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(content)

    return YoutubeCookiesStatusResponse(
        configured=True,
        exists=True,
        path=str(target_path).replace("\\", "/"),
        size_bytes=target_path.stat().st_size,
    )


@router.delete("/youtube-cookies", response_model=YoutubeCookiesStatusResponse)
def delete_youtube_cookies(
    current_user: User = Depends(get_current_user),
) -> YoutubeCookiesStatusResponse:
    target_path = _cookies_target_path()

    if target_path.exists() and target_path.is_file():
        target_path.unlink()

    return YoutubeCookiesStatusResponse(
        configured=True,
        exists=False,
        path=str(target_path).replace("\\", "/"),
        size_bytes=None,
    )