"""add download fields and output media reference

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-17 23:40:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_download_fields"
down_revision: Union[str, None] = "0002_job_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("output_media_asset_id", sa.String(length=36), nullable=True))
    op.add_column("jobs", sa.Column("requested_format", sa.String(length=16), nullable=True))
    op.add_column("jobs", sa.Column("requested_file_name", sa.String(length=255), nullable=True))

    op.create_index(op.f("ix_jobs_output_media_asset_id"), "jobs", ["output_media_asset_id"], unique=False)
    op.create_foreign_key(
        "fk_jobs_output_media_asset_id_media_assets",
        "jobs",
        "media_assets",
        ["output_media_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_jobs_output_media_asset_id_media_assets", "jobs", type_="foreignkey")
    op.drop_index(op.f("ix_jobs_output_media_asset_id"), table_name="jobs")
    op.drop_column("jobs", "requested_file_name")
    op.drop_column("jobs", "requested_format")
    op.drop_column("jobs", "output_media_asset_id")