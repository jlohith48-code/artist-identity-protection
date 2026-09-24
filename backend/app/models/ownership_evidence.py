from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class OwnershipEvidence(Base):
    __tablename__ = "ownership_evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    matched_artist_id = Column(UUID(as_uuid=True), ForeignKey("artists.id"), nullable=True)
    matched_artist_name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False, default="youtube")
    source_url = Column(Text, nullable=False)
    video_title = Column(Text, nullable=True)
    channel_id = Column(String(255), nullable=True)
    channel_confidence = Column(String(20), nullable=False)
    evidence_type = Column(String(30), nullable=False)
    match_type = Column(String(20), nullable=False)
    role = Column(String(30), nullable=True)
    raw_credit_text = Column(Text, nullable=True)
    stage_name_tag = Column(String(255), nullable=True)
    status = Column(String(30), nullable=False, default="pending_review")
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("artists.id"), nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    artist = relationship("Artist", foreign_keys=[matched_artist_id], backref="ownership_evidences")
    reviewer = relationship("Artist", foreign_keys=[reviewed_by_user_id], backref="reviewed_evidences")
