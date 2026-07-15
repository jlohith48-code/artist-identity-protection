from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.artist_profile import ArtistProfile
from app.models.artist import Artist
from app.models.fraud_score import FraudScore
from app.ml.scoring_service import score_profile
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
import uuid

router = APIRouter(prefix="/profiles", tags=["Artist Profiles"])

class ProfileCreate(BaseModel):
    artist_id: uuid.UUID
    platform: str
    platform_profile_id: Optional[str] = None
    profile_url: Optional[str] = None
    claimed_display_name: Optional[str] = None
    is_verified_owner: bool = False
    monthly_listeners: int = 0
    follower_count: int = 0
    total_songs: int = 0
    account_created_date: Optional[date] = None

class ProfileResponse(BaseModel):
    id: uuid.UUID
    artist_id: uuid.UUID
    platform: str
    platform_profile_id: Optional[str] = None
    profile_url: Optional[str] = None
    claimed_display_name: Optional[str] = None
    is_verified_owner: bool
    monthly_listeners: int
    follower_count: int
    total_songs: int
    account_created_date: Optional[date] = None
    first_seen_at: datetime

    class Config:
        from_attributes = True

class FraudScoreResponse(BaseModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    name_similarity_score: float
    account_age_score: float
    growth_velocity_score: float
    metadata_completeness_score: float
    overall_risk_score: float
    risk_label: str
    model_version: str
    scored_at: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=ProfileResponse)
def create_profile(profile: ProfileCreate, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == profile.artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    new_profile = ArtistProfile(**profile.model_dump())
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    try:
        score_result = score_profile(artist.full_name, new_profile)
        fraud_score = FraudScore(
            profile_id=new_profile.id,
            name_similarity_score=score_result["name_similarity_score"],
            account_age_score=score_result["account_age_score"],
            growth_velocity_score=score_result["growth_velocity_score"],
            metadata_completeness_score=score_result["metadata_completeness_score"],
            overall_risk_score=score_result["overall_risk_score"],
            risk_label=score_result["risk_label"],
            model_version="v1",
        )
        db.add(fraud_score)
        db.commit()
    except Exception as e:
        print(f"Scoring failed (non-fatal): {e}")

    return new_profile

@router.get("/", response_model=List[ProfileResponse])
def get_all_profiles(db: Session = Depends(get_db)):
    return db.query(ArtistProfile).all()

@router.get("/artist/{artist_id}", response_model=List[ProfileResponse])
def get_profiles_by_artist(artist_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(ArtistProfile).filter(ArtistProfile.artist_id == artist_id).all()

@router.get("/unverified", response_model=List[ProfileResponse])
def get_unverified_profiles(db: Session = Depends(get_db)):
    return db.query(ArtistProfile).filter(ArtistProfile.is_verified_owner == False).all()

@router.get("/fraud-scores/all")
def get_all_fraud_scores(db: Session = Depends(get_db)):
    scores = db.query(FraudScore).all()
    results = []
    for score in scores:
        profile = db.query(ArtistProfile).filter(ArtistProfile.id == score.profile_id).first()
        artist = db.query(Artist).filter(Artist.id == profile.artist_id).first() if profile else None
        results.append({
            "profile_id": str(score.profile_id),
            "artist_name": artist.full_name if artist else "Unknown",
            "claimed_display_name": profile.claimed_display_name if profile else None,
            "platform": profile.platform if profile else None,
            "is_verified_owner": profile.is_verified_owner if profile else None,
            "monthly_listeners": profile.monthly_listeners if profile else None,
            "follower_count": profile.follower_count if profile else None,
            "overall_risk_score": score.overall_risk_score,
            "risk_label": score.risk_label,
            "name_similarity_score": score.name_similarity_score,
            "account_age_score": score.account_age_score,
            "growth_velocity_score": score.growth_velocity_score,
            "metadata_completeness_score": score.metadata_completeness_score,
            "scored_at": score.scored_at.isoformat(),
        })
    return results

@router.get("/{profile_id}/fraud-score", response_model=FraudScoreResponse)
def get_fraud_score(profile_id: uuid.UUID, db: Session = Depends(get_db)):
    score = db.query(FraudScore).filter(FraudScore.profile_id == profile_id).order_by(FraudScore.scored_at.desc()).first()
    if not score:
        raise HTTPException(status_code=404, detail="No fraud score found for this profile")
    return score

@router.get("/high-risk/list", response_model=List[FraudScoreResponse])
def get_high_risk_profiles(db: Session = Depends(get_db)):
    return db.query(FraudScore).filter(FraudScore.risk_label == "high_risk").order_by(FraudScore.overall_risk_score.desc()).all()
