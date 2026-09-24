"""add pgvector extension and song_embeddings table

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-09-24 02:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

revision: str = 'b4c5d6e7f8a9'
down_revision: Union[str, Sequence[str], None] = 'a3b4c5d6e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Enable pgvector extension if using PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.create_table(
        'song_embeddings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('song_id', sa.UUID(), sa.ForeignKey('songs.id'), nullable=False),
        sa.Column('embedding', Vector(384) if HAS_PGVECTOR and bind.dialect.name == "postgresql" else sa.Text(), nullable=True),
        sa.Column('embedding_json', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False, server_default='all-MiniLM-L6-v2'),
        sa.Column('model_version', sa.String(length=20), nullable=False, server_default='v1'),
        sa.Column('embedding_dimension', sa.Integer(), nullable=False, server_default='384'),
        sa.Column('chunk_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chunk_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('idx_song_embeddings_song_id', 'song_embeddings', ['song_id'])

    if bind.dialect.name == "postgresql":
        op.execute("CREATE INDEX IF NOT EXISTS idx_song_embeddings_hnsw ON song_embeddings USING hnsw (embedding vector_cosine_ops);")

def downgrade() -> None:
    op.drop_index('idx_song_embeddings_song_id', table_name='song_embeddings')
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS idx_song_embeddings_hnsw;")
    op.drop_table('song_embeddings')
