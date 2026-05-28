"""add transcription tables and fields

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-18 20:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("transcription_media_asset_id", sa.String(length=36), nullable=True))
    op.create_index(
        op.f("ix_jobs_transcription_media_asset_id"),
        "jobs",
        ["transcription_media_asset_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_jobs_transcription_media_asset_id_media_assets",
        "jobs",
        "media_assets",
        ["transcription_media_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "transcripts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("media_asset_id", sa.String(length=36), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("engine", sa.String(length=64), nullable=False),
        sa.Column("full_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_asset_id"], ["media_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transcripts_job_id"), "transcripts", ["job_id"], unique=False)
    op.create_index(op.f("ix_transcripts_media_asset_id"), "transcripts", ["media_asset_id"], unique=False)

    op.create_table(
        "transcript_segments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("transcript_id", sa.String(length=36), nullable=False),
        sa.Column("start_sec", sa.Integer(), nullable=False),
        sa.Column("end_sec", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("speaker_label", sa.String(length=64), nullable=True),
        sa.Column("confidence", sa.String(length=32), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["transcript_id"], ["transcripts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transcript_segments_transcript_id"), "transcript_segments", ["transcript_id"], unique=False)

    op.create_table(
        "export_artifacts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("transcript_id", sa.String(length=36), nullable=False),
        sa.Column("format", sa.String(length=16), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["transcript_id"], ["transcripts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_export_artifacts_transcript_id"), "export_artifacts", ["transcript_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_export_artifacts_transcript_id"), table_name="export_artifacts")
    op.drop_table("export_artifacts")

    op.drop_index(op.f("ix_transcript_segments_transcript_id"), table_name="transcript_segments")
    op.drop_table("transcript_segments")

    op.drop_index(op.f("ix_transcripts_media_asset_id"), table_name="transcripts")
    op.drop_index(op.f("ix_transcripts_job_id"), table_name="transcripts")
    op.drop_table("transcripts")

    op.drop_constraint("fk_jobs_transcription_media_asset_id_media_assets", "jobs", type_="foreignkey")
    op.drop_index(op.f("ix_jobs_transcription_media_asset_id"), table_name="jobs")
    op.drop_column("jobs", "transcription_media_asset_id")