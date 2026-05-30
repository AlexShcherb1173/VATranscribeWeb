"""security privacy foundation"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '20260529_sec_priv_found'
down_revision = '20260524_0004_lyrics'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'legal_documents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('document_type', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_legal_documents_type_version', 'legal_documents', ['document_type', 'version'], unique=True)
    op.create_index('ix_legal_documents_document_type', 'legal_documents', ['document_type'], unique=False)

    op.create_table(
        'user_consents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('document_type', sa.String(length=100), nullable=False),
        sa.Column('document_version', sa.String(length=50), nullable=False),
        sa.Column('accepted', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('ip_hash', sa.String(length=128), nullable=True),
        sa.Column('user_agent_hash', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_user_consents_user_id', 'user_consents', ['user_id'], unique=False)
    op.create_index('ix_user_consents_user_doc_version', 'user_consents', ['user_id', 'document_type', 'document_version'], unique=False)

    op.create_table(
        'privacy_requests',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('request_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_privacy_requests_user_id', 'privacy_requests', ['user_id'], unique=False)
    op.create_index('ix_privacy_requests_status', 'privacy_requests', ['status'], unique=False)

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('actor_user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=150), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('meta_json', sa.JSON(), nullable=True),
        sa.Column('ip_hash', sa.String(length=128), nullable=True),
        sa.Column('user_agent_hash', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_audit_logs_actor_user_id', 'audit_logs', ['actor_user_id'], unique=False)
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'], unique=False)

    op.create_table(
        'security_events',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('event_type', sa.String(length=150), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('meta_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_security_events_user_id', 'security_events', ['user_id'], unique=False)
    op.create_index('ix_security_events_event_type', 'security_events', ['event_type'], unique=False)

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False, unique=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index('ix_security_events_event_type', table_name='security_events')
    op.drop_index('ix_security_events_user_id', table_name='security_events')
    op.drop_table('security_events')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_actor_user_id', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('ix_privacy_requests_status', table_name='privacy_requests')
    op.drop_index('ix_privacy_requests_user_id', table_name='privacy_requests')
    op.drop_table('privacy_requests')
    op.drop_index('ix_user_consents_user_doc_version', table_name='user_consents')
    op.drop_index('ix_user_consents_user_id', table_name='user_consents')
    op.drop_table('user_consents')
    op.drop_index('ix_legal_documents_document_type', table_name='legal_documents')
    op.drop_index('ix_legal_documents_type_version', table_name='legal_documents')
    op.drop_table('legal_documents')

