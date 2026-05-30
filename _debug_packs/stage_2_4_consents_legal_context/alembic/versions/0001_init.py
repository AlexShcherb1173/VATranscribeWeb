"""init jobs users media assets

Revision ID: 0001_init_jobs_users_media_assets
Revises: None
Create Date: 2026-04-17 22:40:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("input_url", sa.Text(), nullable=True),
        sa.Column("selected_video_format_id", sa.String(length=64), nullable=True),
        sa.Column("selected_audio_format_id", sa.String(length=64), nullable=True),
        sa.Column("download_audio", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("download_video", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("transcription_model", sa.String(length=64), nullable=True),
        sa.Column("transcription_language", sa.String(length=16), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_jobs_status"), "jobs", ["status"], unique=False)
    op.create_index(op.f("ix_jobs_type"), "jobs", ["type"], unique=False)
    op.create_index(op.f("ix_jobs_user_id"), "jobs", ["user_id"], unique=False)

    op.create_table(
        "media_assets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("stored_name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("extension", sa.String(length=32), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_sec", sa.Integer(), nullable=True),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_media_assets_kind"), "media_assets", ["kind"], unique=False)
    op.create_index(op.f("ix_media_assets_user_id"), "media_assets", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_media_assets_user_id"), table_name="media_assets")
    op.drop_index(op.f("ix_media_assets_kind"), table_name="media_assets")
    op.drop_table("media_assets")

    op.drop_index(op.f("ix_jobs_user_id"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_type"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_status"), table_name="jobs")
    op.drop_table("jobs")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")