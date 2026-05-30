"""add user profile and quota tables

Revision ID: XXXX_add_user_profile_and_quota_tables
Revises: PREVIOUS_REVISION_ID
Create Date: 2026-04-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),

        sa.Column("full_name", sa.String(length=255)),
        sa.Column("company_name", sa.String(length=255)),
        sa.Column("timezone", sa.String(length=64)),
        sa.Column("locale", sa.String(length=32)),
        sa.Column("avatar_url", sa.String(length=1024)),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id"),
    )

    op.create_index(
        "ix_user_profiles_user_id",
        "user_profiles",
        ["user_id"],
    )

    op.create_table(
        "user_quotas",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),

        sa.Column("storage_bytes_used", sa.BigInteger(), server_default="0"),
        sa.Column("transcription_seconds_used", sa.Integer(), server_default="0"),
        sa.Column("jobs_count_used", sa.Integer(), server_default="0"),

        sa.Column(
            "storage_bytes_limit",
            sa.BigInteger(),
            server_default=str(10 * 1024 * 1024 * 1024),
        ),
        sa.Column(
            "transcription_seconds_limit",
            sa.Integer(),
            server_default=str(10 * 60 * 60),
        ),
        sa.Column("jobs_count_limit", sa.Integer(), server_default="500"),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id"),
    )

    op.create_index(
        "ix_user_quotas_user_id",
        "user_quotas",
        ["user_id"],
    )