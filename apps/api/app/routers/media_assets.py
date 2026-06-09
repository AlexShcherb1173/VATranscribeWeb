from __future__ import annotations


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from apps.api.app.config import settings
from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import MediaAsset, Transcript, User
from apps.api.app.schemas import MediaAssetResponse
from apps.api.app.services.quota_service import sync_storage_usage_from_media_assets
from apps.api.app.services.storage_limits import assert_path_size_within_limit
from packages.core.vatranscribe_core.storage import resolve_storage_path

router = APIRouter(prefix="/media-assets", tags=["Media assets"])


def _build_media_asset_response(item: MediaAsset) -> MediaAssetResponse:
    return MediaAssetResponse(
        id=item.id,
        kind=item.kind,
        original_name=item.original_name,
        stored_name=item.stored_name,
        mime_type=item.mime_type,
        extension=item.extension,
        size_bytes=item.size_bytes,
        duration_sec=item.duration_sec,
        checksum_sha256=item.checksum_sha256,
        created_at=item.created_at,
        download_url=f"/media-assets/{item.id}/download",
    )


def _get_media_asset_or_404(
    media_asset_id: str,
    db: Session,
    current_user: User,
) -> MediaAsset:
    stmt = (
        select(MediaAsset)
        .options(selectinload(MediaAsset.transcripts).selectinload(Transcript.export_artifacts))
        .where(
            MediaAsset.id == media_asset_id,
            MediaAsset.user_id == current_user.id,
        )
    )
    item = db.scalar(stmt)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media asset '{media_asset_id}' not found",
        )
    return item


@router.get("", response_model=list[MediaAssetResponse], summary="List media assets")
def list_media_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MediaAssetResponse]:
    items = db.scalars(
        select(MediaAsset)
        .where(MediaAsset.user_id == current_user.id)
        .order_by(MediaAsset.created_at.desc())
    ).all()
    return [_build_media_asset_response(item) for item in items]


@router.get("/{media_asset_id}", response_model=MediaAssetResponse, summary="Get media asset by id")
def get_media_asset(
    media_asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MediaAssetResponse:
    return _build_media_asset_response(_get_media_asset_or_404(media_asset_id, db, current_user))


@router.get("/{media_asset_id}/download", summary="Download media asset file")
def download_media_asset(
    media_asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = _get_media_asset_or_404(media_asset_id, db, current_user)
    file_path = resolve_storage_path(item.path)

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media asset file for '{media_asset_id}' not found on disk",
        )

    assert_path_size_within_limit(file_path, settings.max_media_download_bytes, "Media asset download")

    return FileResponse(
        path=file_path,
        media_type=item.mime_type or "application/octet-stream",
        filename=item.stored_name,
    )


@router.delete("/{media_asset_id}", status_code=status.HTTP_200_OK, summary="Delete media asset")
def delete_media_asset(
    media_asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    item = _get_media_asset_or_404(media_asset_id, db, current_user)

    # Delete transcript export files first. DB cascades rows, but not files on disk.
    for transcript in item.transcripts:
        for artifact in transcript.export_artifacts:
            artifact_path = resolve_storage_path(artifact.path)
            if artifact_path.exists() and artifact_path.is_file():
                artifact_path.unlink(missing_ok=True)

    media_path = resolve_storage_path(item.path)
    if media_path.exists() and media_path.is_file():
        media_path.unlink(missing_ok=True)

    db.delete(item)
    db.commit()

    sync_storage_usage_from_media_assets(db, current_user)

    return {"status": "ok", "message": f"Media asset '{media_asset_id}' deleted"}
