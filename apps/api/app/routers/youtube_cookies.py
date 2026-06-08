from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from apps.api.app.config import get_settings
from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import User
from apps.api.app.schemas import YouTubeCookiesStatusResponse
from apps.api.app.services.youtube_cookies_service import (
    delete_youtube_cookies,
    get_youtube_cookies_status,
    upsert_youtube_cookies,
)

router = APIRouter(prefix="/youtube-cookies", tags=["youtube-cookies"])


@router.get(
    "/status",
    response_model=YouTubeCookiesStatusResponse,
    summary="Get current user's YouTube cookies status",
)
def get_my_youtube_cookies_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> YouTubeCookiesStatusResponse:
    return YouTubeCookiesStatusResponse(**get_youtube_cookies_status(db, current_user))


@router.post(
    "",
    response_model=YouTubeCookiesStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload current user's YouTube cookies.txt",
)
async def upload_my_youtube_cookies(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> YouTubeCookiesStatusResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required",
        )

    settings = get_settings()
    content = await file.read(settings.youtube_cookies_max_bytes + 1)
    await file.close()

    row = upsert_youtube_cookies(
        db,
        current_user,
        content=content,
        source_filename=file.filename,
    )

    return YouTubeCookiesStatusResponse(
        configured=True,
        source_filename=row.source_filename,
        cookie_format=row.cookie_format,
        size_bytes=row.size_bytes,
        updated_at=row.updated_at,
    )


@router.delete(
    "",
    response_model=YouTubeCookiesStatusResponse,
    summary="Delete current user's YouTube cookies",
)
def delete_my_youtube_cookies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> YouTubeCookiesStatusResponse:
    delete_youtube_cookies(db, current_user)
    return YouTubeCookiesStatusResponse(configured=False)
