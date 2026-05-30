from __future__ import annotations

from alembic import op


revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE jobs
        ADD COLUMN IF NOT EXISTS progress_percent INTEGER NOT NULL DEFAULT 0;
        """
    )

    op.execute(
        """
        ALTER TABLE jobs
        ADD COLUMN IF NOT EXISTS progress_stage VARCHAR(64);
        """
    )

    op.execute(
        """
        ALTER TABLE jobs
        ADD COLUMN IF NOT EXISTS progress_message VARCHAR(512);
        """
    )

    op.execute(
        """
        ALTER TABLE jobs
        ALTER COLUMN progress_percent DROP DEFAULT;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE jobs
        DROP COLUMN IF EXISTS progress_message;
        """
    )

    op.execute(
        """
        ALTER TABLE jobs
        DROP COLUMN IF EXISTS progress_stage;
        """
    )

    op.execute(
        """
        ALTER TABLE jobs
        DROP COLUMN IF EXISTS progress_percent;
        """
    )