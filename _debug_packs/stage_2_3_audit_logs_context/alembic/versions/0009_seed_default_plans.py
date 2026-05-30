from alembic import op
import sqlalchemy as sa


revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    plans = [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "code": "free",
            "name": "Free",
            "price_monthly": 0,
            "currency": "USD",
            "storage_bytes_limit": 10 * 1024 * 1024 * 1024,
            "transcription_seconds_limit": 36_000,
            "jobs_count_limit": 500,
        },
        {
            "id": "00000000-0000-0000-0000-000000000002",
            "code": "pro",
            "name": "Pro",
            "price_monthly": 12,
            "currency": "USD",
            "storage_bytes_limit": 100 * 1024 * 1024 * 1024,
            "transcription_seconds_limit": 144_000,
            "jobs_count_limit": 5_000,
        },
        {
            "id": "00000000-0000-0000-0000-000000000003",
            "code": "business",
            "name": "Business",
            "price_monthly": 49,
            "currency": "USD",
            "storage_bytes_limit": 500 * 1024 * 1024 * 1024,
            "transcription_seconds_limit": 720_000,
            "jobs_count_limit": 20_000,
        },
    ]

    for plan in plans:
        conn.execute(
            sa.text(
                """
                INSERT INTO plans (
                    id,
                    code,
                    name,
                    price_monthly,
                    currency,
                    storage_bytes_limit,
                    transcription_seconds_limit,
                    jobs_count_limit,
                    is_active,
                    created_at
                )
                VALUES (
                    :id,
                    :code,
                    :name,
                    :price_monthly,
                    :currency,
                    :storage_bytes_limit,
                    :transcription_seconds_limit,
                    :jobs_count_limit,
                    true,
                    now()
                )
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    price_monthly = EXCLUDED.price_monthly,
                    currency = EXCLUDED.currency,
                    storage_bytes_limit = EXCLUDED.storage_bytes_limit,
                    transcription_seconds_limit = EXCLUDED.transcription_seconds_limit,
                    jobs_count_limit = EXCLUDED.jobs_count_limit,
                    is_active = EXCLUDED.is_active
                """
            ),
            plan,
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM plans
            WHERE code IN ('free', 'pro', 'business')
            """
        )
    )