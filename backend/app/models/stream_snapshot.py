from sqlalchemy import Column, Integer, Float, Date, Boolean, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class StreamSnapshot(Base):
    __tablename__ = "stream_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    song_id = Column(UUID(as_uuid=True), ForeignKey("songs.id"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    stream_count = Column(Integer, default=0)
    daily_delta = Column(Integer, default=0)
    growth_rate = Column(Float, default=0.0)
    top_country = Column(String, nullable=True)
    flagged_anomaly = Column(Boolean, default=False)

    song = relationship("Song", backref="stream_snapshots")
