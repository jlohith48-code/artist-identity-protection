from sqlalchemy import Column, Float, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class FraudScore(Base):
    __tablename__ = "fraud_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("artist_profiles.id"), nullable=False)
    name_similarity_score = Column(Float, default=0.0)
    account_age_score = Column(Float, default=0.0)
    growth_velocity_score = Column(Float, default=0.0)
    metadata_completeness_score = Column(Float, default=0.0)
    overall_risk_score = Column(Float, default=0.0)
    risk_label = Column(String, default="unknown")
    model_version = Column(String, default="v1")
    scored_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("ArtistProfile", backref="fraud_scores")
