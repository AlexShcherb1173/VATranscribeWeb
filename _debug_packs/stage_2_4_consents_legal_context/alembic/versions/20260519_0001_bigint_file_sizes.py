"""Use BIGINT for file and storage byte counters.

Revision ID: 20260519_0001_bigint_file_sizes
Revises: 0012_add_job_progress_fields
Create Date: 2026-05-19
"""

from alembic import op
import sqlalchemy as sa


revision = "20260519_0001_bigint_file_sizes"
down_revision = "0012"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if table_name not in inspector.get_table_names():
        return False

    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _alter_to_bigint(table_name: str, column_name: str) -> None:
    if not _has_column(table_name, column_name):
        return

    op.alter_column(
        table_name,
        column_name,
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        postgresql_using=f"{column_name}::bigint",
        existing_nullable=True,
    )


def _alter_to_integer(table_name: str, column_name: str) -> None:
    if not _has_column(table_name, column_name):
        return

    op.alter_column(
        table_name,
        column_name,
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        postgresql_using=f"{column_name}::integer",
        existing_nullable=True,
    )


def upgrade() -> None:
    _alter_to_bigint("media_assets", "size_bytes")

    _alter_to_bigint("user_quotas", "storage_bytes_used")
    _alter_to_bigint("user_quotas", "storage_bytes_limit")

    _alter_to_bigint("usage_snapshots", "storage_bytes_used")

    _alter_to_bigint("plans", "storage_bytes_limit")


def downgrade() -> None:
    _alter_to_integer("plans", "storage_bytes_limit")

    _alter_to_integer("usage_snapshots", "storage_bytes_used")

    _alter_to_integer("user_quotas", "storage_bytes_limit")
    _alter_to_integer("user_quotas", "storage_bytes_used")

    _alter_to_integer("media_assets", "size_bytes")



