"""add mp4_mode field to jobs

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-18 19:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, None] = "0003_download_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("mp4_mode", sa.String(length=32), nullable=True))
    op.execute("UPDATE jobs SET mp4_mode = 'compatible' WHERE mp4_mode IS NULL")


def downgrade() -> None:
    op.drop_column("jobs", "mp4_mode")