"""add job_logs table

Revision ID: 0002_add_job_logs
Revises: 0001_init_jobs_users_media_assets
Create Date: 2026-04-17 23:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_job_logs"
down_revision: Union[str, None] = "0001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_logs_job_id"), "job_logs", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_job_logs_job_id"), table_name="job_logs")
    op.drop_table("job_logs")