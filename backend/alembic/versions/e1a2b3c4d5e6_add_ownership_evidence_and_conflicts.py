"""add ownership evidence and conflicts tables

Revision ID: e1a2b3c4d5e6
Revises: bc4617591876
Create Date: 2026-09-24 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'bc4617591876'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'ownership_evidence',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('matched_artist_id', sa.UUID(), sa.ForeignKey('artists.id'), nullable=True),
        sa.Column('matched_artist_name', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False, server_default='youtube'),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('video_title', sa.Text(), nullable=True),
        sa.Column('channel_id', sa.String(length=255), nullable=True),
        sa.Column('channel_confidence', sa.String(length=20), nullable=False),
        sa.Column('evidence_type', sa.String(length=30), nullable=False),
        sa.Column('match_type', sa.String(length=20), nullable=False),
        sa.Column('role', sa.String(length=30), nullable=True),
        sa.Column('raw_credit_text', sa.Text(), nullable=True),
        sa.Column('stage_name_tag', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending_review'),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_ownership_evidence_status', 'ownership_evidence', ['status'])
    op.create_index('idx_ownership_evidence_artist', 'ownership_evidence', ['matched_artist_id'])

    op.create_table(
        'ownership_conflicts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('song_id', sa.UUID(), sa.ForeignKey('songs.id'), nullable=True),
        sa.Column('claiming_profile_id', sa.UUID(), sa.ForeignKey('artist_profiles.id'), nullable=True),
        sa.Column('true_owner_artist_id', sa.UUID(), sa.ForeignKey('artists.id'), nullable=True),
        sa.Column('true_owner_claimed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('conflict_type', sa.String(length=50), nullable=False),
        sa.Column('evidence_id', sa.Integer(), sa.ForeignKey('ownership_evidence.id'), nullable=True),
        sa.Column('flagged_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('resolved', sa.Boolean(), server_default=sa.text('false')),
    )

def downgrade() -> None:
    op.drop_table('ownership_conflicts')
    op.drop_index('idx_ownership_evidence_artist', table_name='ownership_evidence')
    op.drop_index('idx_ownership_evidence_status', table_name='ownership_evidence')
    op.drop_table('ownership_evidence')
