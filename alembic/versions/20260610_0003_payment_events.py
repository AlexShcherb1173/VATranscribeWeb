"""add payment events for billing production gate

Revision ID: 20260610_0003
Revises: 20260610_0002
Create Date: 2026-06-10
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260610_0003"
down_revision: Union[str, None] = "20260610_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column("provider_event_key", sa.String(length=320), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="received"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_event_key"),
    )
    op.create_index("ix_payment_events_provider", "payment_events", ["provider"], unique=False)
    op.create_index("ix_payment_events_event_type", "payment_events", ["event_type"], unique=False)
    op.create_index("ix_payment_events_provider_event_key", "payment_events", ["provider_event_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_payment_events_provider_event_key", table_name="payment_events")
    op.drop_index("ix_payment_events_event_type", table_name="payment_events")
    op.drop_index("ix_payment_events_provider", table_name="payment_events")
    op.drop_table("payment_events")
