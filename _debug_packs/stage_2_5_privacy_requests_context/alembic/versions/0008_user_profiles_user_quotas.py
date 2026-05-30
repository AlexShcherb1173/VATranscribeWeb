"""legacy no-op: profile and quota tables are created in revision 0006.

Revision ID: 0008
Revises: 0007
"""

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Kept intentionally empty to preserve the migration chain.
    # The previous implementation attempted to create user_profiles/user_quotas
    # for a second time after revision 0006, which breaks clean database setup.
    pass


def downgrade() -> None:
    pass
