from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.artist import Artist
from app.schemas import ArtistCreate, ArtistResponse
from app.utils.security import get_current_user_optional, require_admin
from typing import List, Optional

router = APIRouter(prefix="/artists", tags=["Artists"])

@router.post("/", response_model=ArtistResponse)
def create_artist(artist: ArtistCreate, db: Session = Depends(get_db)):
    new_artist = Artist(
        full_name=artist.full_name,
        email=artist.email.lower(),
        phone=artist.phone,
        iprs_id=artist.iprs_id,
        state=artist.state,
    )
    db.add(new_artist)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="An artist with this email already exists")
    db.refresh(new_artist)
    return new_artist

@router.get("/", response_model=List[ArtistResponse])
def get_all_artists(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    artists = db.query(Artist).offset(skip).limit(limit).all()
    
    # If not authenticated or non-admin, sanitize sensitive PII fields
    is_admin = current_user and current_user.get("role") == "admin"
    if not is_admin:
        sanitized = []
        for a in artists:
            # Hide email and phone for non-owner/non-admin public list
            a_dict = {
                "id": a.id,
                "full_name": a.full_name,
                "email": a.email if (current_user and current_user.get("sub") == str(a.id)) else "***@***",
                "phone": a.phone if (current_user and current_user.get("sub") == str(a.id)) else None,
                "iprs_id": a.iprs_id if (current_user and current_user.get("sub") == str(a.id)) else None,
                "state": a.state,
                "created_at": a.created_at
            }
            sanitized.append(a_dict)
        return sanitized
    return artists

@router.get("/{artist_id}", response_model=ArtistResponse)
def get_artist(artist_id: str, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    return artist
