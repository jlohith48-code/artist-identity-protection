"""add status and reviewer attribution to ownership conflicts

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-09-24 02:38:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c5d6e7f8a9b0'
down_revision: Union[str, Sequence[str], None] = 'b4c5d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('ownership_conflicts', sa.Column('status', sa.String(length=30), nullable=False, server_default='pending_review'))
    op.add_column('ownership_conflicts', sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.add_column('ownership_conflicts', sa.Column('reviewed_by_user_id', sa.UUID(), sa.ForeignKey('artists.id'), nullable=True))
    op.create_index('idx_ownership_conflicts_status', 'ownership_conflicts', ['status'])

def downgrade() -> None:
    op.drop_index('idx_ownership_conflicts_status', table_name='ownership_conflicts')
    op.drop_column('ownership_conflicts', 'reviewed_by_user_id')
    op.drop_column('ownership_conflicts', 'reviewed_at')
    op.drop_column('ownership_conflicts', 'status')
