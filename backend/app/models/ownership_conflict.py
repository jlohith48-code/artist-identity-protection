from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class OwnershipConflict(Base):
    __tablename__ = "ownership_conflicts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    song_id = Column(UUID(as_uuid=True), ForeignKey("songs.id"), nullable=True)
    claiming_profile_id = Column(UUID(as_uuid=True), ForeignKey("artist_profiles.id"), nullable=True)
    true_owner_artist_id = Column(UUID(as_uuid=True), ForeignKey("artists.id"), nullable=True)
    true_owner_claimed = Column(Boolean, nullable=False, default=False)
    conflict_type = Column(String(50), nullable=False)
    evidence_id = Column(Integer, ForeignKey("ownership_evidence.id"), nullable=True)
    status = Column(String(30), nullable=False, default="pending_review")
    flagged_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("artists.id"), nullable=True)

    song = relationship("Song", backref="conflicts")
    claiming_profile = relationship("ArtistProfile", backref="conflicts")
    true_owner_artist = relationship("Artist", foreign_keys=[true_owner_artist_id], backref="ownership_conflicts")
    evidence = relationship("OwnershipEvidence", backref="conflicts")
    reviewer = relationship("Artist", foreign_keys=[reviewed_by_user_id], backref="reviewed_conflicts")
