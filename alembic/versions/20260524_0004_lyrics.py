"""add lyrics quality fields

Revision ID: 20260524_0004_lyrics
Revises: 20260524_0003_tx_profile
Create Date: 2026-05-24 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260524_0004_lyrics"
down_revision = "20260524_0003_tx_profile"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    columns = [
        ("duration_sec", sa.Column("duration_sec", sa.Integer(), nullable=True)),
        ("segments_count", sa.Column("segments_count", sa.Integer(), nullable=True)),
        ("coverage_sec", sa.Column("coverage_sec", sa.Integer(), nullable=True)),
        ("coverage_ratio", sa.Column("coverage_ratio", sa.String(length=32), nullable=True)),
        ("quality_status", sa.Column("quality_status", sa.String(length=32), nullable=True)),
        ("quality_warning", sa.Column("quality_warning", sa.Text(), nullable=True)),
    ]

    for column_name, column in columns:
        if not _has_column("transcripts", column_name):
            op.add_column("transcripts", column)


def downgrade() -> None:
    for column_name in [
        "quality_warning",
        "quality_status",
        "coverage_ratio",
        "coverage_sec",
        "segments_count",
        "duration_sec",
    ]:
        if _has_column("transcripts", column_name):
            op.drop_column("transcripts", column_name)
