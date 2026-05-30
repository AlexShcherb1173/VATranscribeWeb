"""Add job heartbeat and last log fields.

Revision ID: 20260521_0002_job_heartbeat
Revises: 20260519_0001_bigint_file_sizes
Create Date: 2026-05-21
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260521_0002_job_heartbeat"
down_revision = "20260519_0001_bigint_file_sizes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("last_log_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("last_log_message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "last_log_message")
    op.drop_column("jobs", "last_log_at")
    op.drop_column("jobs", "heartbeat_at")
