from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.database import get_db
from apps.api.app.dependencies import get_current_user
from apps.api.app.models import ExportArtifact, MediaAsset, Transcript, User
from apps.api.app.schemas import ExportArtifactResponse

router = APIRouter(prefix="/export-artifacts")


def _get_export_artifact_or_404(
    artifact_id: str,
    db: Session,
    current_user: User,
) -> ExportArtifact:
    stmt = (
        select(ExportArtifact)
        .join(Transcript, ExportArtifact.transcript_id == Transcript.id)
        .join(MediaAsset, Transcript.media_asset_id == MediaAsset.id)
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


@router.get(
    "/{artifact_id}",
    response_model=ExportArtifactResponse,
    summary="Get export artifact by id",
)
def get_export_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExportArtifactResponse:
    item = _get_export_artifact_or_404(artifact_id, db, current_user)

    return ExportArtifactResponse(
        id=item.id,
        transcript_id=item.transcript_id,
        format=item.format,
        path=item.path,
        size_bytes=item.size_bytes,
        created_at=item.created_at,
        download_url=f"/api/v1/export-artifacts/{item.id}/download",
    )


@router.get(
    "/{artifact_id}/download",
    summary="Download export artifact file",
)
def download_export_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = _get_export_artifact_or_404(artifact_id, db, current_user)

    file_path = Path(item.path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export artifact file for '{artifact_id}' not found on disk",
        )

    media_type_map = {
        "txt": "text/plain",
        "srt": "application/x-subrip",
        "vtt": "text/vtt",
        "json": "application/json",
    }

    return FileResponse(
        path=file_path,
        media_type=media_type_map.get(item.format, "application/octet-stream"),
        filename=file_path.name,
    )


@router.delete(
    "/{artifact_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete export artifact",
)
def delete_export_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    item = _get_export_artifact_or_404(artifact_id, db, current_user)

    file_path = Path(item.path)
    if file_path.exists() and file_path.is_file():
        file_path.unlink(missing_ok=True)

    db.delete(item)
    db.commit()

    return {
        "status": "ok",
        "message": f"Export artifact '{artifact_id}' deleted",
    }