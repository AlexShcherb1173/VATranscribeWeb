"""add users.updated_at.

Revision ID: 0010
Revises: 0009
"""

from alembic import op


revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now()
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS updated_at")
