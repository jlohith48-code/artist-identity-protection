from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.artist_profile import ArtistProfile
from app.models.artist import Artist
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
    is_verified_owner: bool
    monthly_listeners: int
    follower_count: int
    total_songs: int
    account_created_date: Optional[date] = None
    first_seen_at: datetime

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
