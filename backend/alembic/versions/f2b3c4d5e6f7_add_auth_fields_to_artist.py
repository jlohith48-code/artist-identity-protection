"""add auth fields to artist table

Revision ID: f2b3c4d5e6f7
Revises: e1a2b3c4d5e6
Create Date: 2026-09-24 02:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f2b3c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = 'e1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('artists', sa.Column('hashed_password', sa.String(), nullable=True))
    op.add_column('artists', sa.Column('role', sa.String(), server_default='artist', nullable=False))

def downgrade() -> None:
    op.drop_column('artists', 'role')
    op.drop_column('artists', 'hashed_password')
