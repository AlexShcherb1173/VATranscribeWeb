"""add transcription profile to jobs

Revision ID: 20260524_0003_tx_profile
Revises: 20260521_0002_job_heartbeat
Create Date: 2026-05-24 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260524_0003_tx_profile"
down_revision = "20260521_0002_job_heartbeat"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("transcription_profile", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("jobs", "transcription_profile")

