from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

class SongEmbedding(Base):
    __tablename__ = "song_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    song_id = Column(UUID(as_uuid=True), ForeignKey("songs.id"), nullable=False)
    
    if HAS_PGVECTOR:
        embedding = Column(Vector(384), nullable=True)
    else:
        embedding = Column(Text, nullable=True)

    embedding_json = Column(Text, nullable=True)
    model_name = Column(String(100), nullable=False, default="all-MiniLM-L6-v2")
    model_version = Column(String(20), nullable=False, default="v1")
    embedding_dimension = Column(Integer, nullable=False, default=384)
    chunk_index = Column(Integer, nullable=False, default=0)
    chunk_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    song = relationship("Song", backref="embeddings")
