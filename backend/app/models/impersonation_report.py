from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class ImpersonationReport(Base):
    __tablename__ = "impersonation_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artist_id = Column(UUID(as_uuid=True), ForeignKey("artists.id"), nullable=False)
    fake_profile_id = Column(UUID(as_uuid=True), ForeignKey("artist_profiles.id"), nullable=False)
    status = Column(String, default="pending")
    evidence_summary = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    artist = relationship("Artist", backref="reports")
    fake_profile = relationship("ArtistProfile", backref="reports")
