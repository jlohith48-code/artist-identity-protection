from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class ArtistProfile(Base):
    __tablename__ = "artist_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artist_id = Column(UUID(as_uuid=True), ForeignKey("artists.id"), nullable=False)
    platform = Column(String, nullable=False)
    platform_profile_id = Column(String, nullable=True)
    profile_url = Column(String, nullable=True)
    claimed_display_name = Column(String, nullable=True)
    is_verified_owner = Column(Boolean, default=False)
    monthly_listeners = Column(Integer, default=0)
    follower_count = Column(Integer, default=0)
    total_songs = Column(Integer, default=0)
    account_created_date = Column(Date, nullable=True)
    first_seen_at = Column(DateTime, default=datetime.utcnow)

    artist = relationship("Artist", backref="profiles")
