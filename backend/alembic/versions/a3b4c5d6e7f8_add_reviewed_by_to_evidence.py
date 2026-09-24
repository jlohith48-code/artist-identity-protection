"""add reviewed_by_user_id to ownership_evidence

Revision ID: a3b4c5d6e7f8
Revises: f2b3c4d5e6f7
Create Date: 2026-09-24 02:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, Sequence[str], None] = 'f2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('ownership_evidence', sa.Column('reviewed_by_user_id', sa.UUID(), sa.ForeignKey('artists.id'), nullable=True))

def downgrade() -> None:
    op.drop_column('ownership_evidence', 'reviewed_by_user_id')
