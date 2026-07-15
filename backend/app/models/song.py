from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class Song(Base):
    __tablename__ = "songs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artist_id = Column(UUID(as_uuid=True), ForeignKey("artists.id"), nullable=False)
    title = Column(String, nullable=False)
    language = Column(String, nullable=True)
    lyrics_hash = Column(String, nullable=False)
    lyrics_preview = Column(String, nullable=True)
    lyrics_vector = Column(Text, nullable=True)
    youtube_url = Column(String, nullable=True)
    production_house = Column(String, nullable=True)
    written_on = Column(Date, nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)

    artist = relationship("Artist", backref="songs")
