"""sync runtime schema with current ORM models.

Revision ID: 0011
Revises: 0010
"""

from alembic import op


revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now()")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true")

    op.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS output_media_asset_id varchar(36)")
    op.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS requested_format varchar(16)")
    op.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS requested_file_name varchar(255)")
    op.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS mp4_mode varchar(32)")
    op.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS transcription_media_asset_id varchar(36)")

    op.execute("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS full_name varchar(255)")
    op.execute("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS avatar_url varchar(1024)")
    op.execute("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now()")
    op.execute("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now()")

    op.execute("ALTER TABLE user_quotas ADD COLUMN IF NOT EXISTS storage_bytes_used bigint NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE user_quotas ADD COLUMN IF NOT EXISTS transcription_seconds_used integer NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE user_quotas ADD COLUMN IF NOT EXISTS jobs_count_used integer NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE user_quotas ADD COLUMN IF NOT EXISTS storage_bytes_limit bigint NOT NULL DEFAULT 10737418240")
    op.execute("ALTER TABLE user_quotas ADD COLUMN IF NOT EXISTS transcription_seconds_limit integer NOT NULL DEFAULT 36000")
    op.execute("ALTER TABLE user_quotas ADD COLUMN IF NOT EXISTS jobs_count_limit integer NOT NULL DEFAULT 500")
    op.execute("ALTER TABLE user_quotas ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now()")
    op.execute("ALTER TABLE user_quotas ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now()")

    op.execute(
        """
        INSERT INTO plans (
            id, code, name, price_monthly, currency,
            storage_bytes_limit, transcription_seconds_limit,
            jobs_count_limit, is_active, created_at
        ) VALUES
            ('00000000-0000-0000-0000-000000000001', 'free', 'Free', 0, 'USD', 10737418240, 36000, 500, true, now()),
            ('00000000-0000-0000-0000-000000000002', 'pro', 'Pro', 12, 'USD', 107374182400, 144000, 5000, true, now()),
            ('00000000-0000-0000-0000-000000000003', 'business', 'Business', 49, 'USD', 536870912000, 720000, 20000, true, now())
        ON CONFLICT (code) DO UPDATE SET
            name = EXCLUDED.name,
            price_monthly = EXCLUDED.price_monthly,
            currency = EXCLUDED.currency,
            storage_bytes_limit = EXCLUDED.storage_bytes_limit,
            transcription_seconds_limit = EXCLUDED.transcription_seconds_limit,
            jobs_count_limit = EXCLUDED.jobs_count_limit,
            is_active = EXCLUDED.is_active
        """
    )


def downgrade() -> None:
    # Safety migration. Do not destructively drop app columns on downgrade.
    pass
