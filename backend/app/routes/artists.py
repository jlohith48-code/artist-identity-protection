from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.artist import Artist
from app.schemas import ArtistCreate, ArtistResponse
from typing import List

router = APIRouter(prefix="/artists", tags=["Artists"])

@router.post("/", response_model=ArtistResponse)
def create_artist(artist: ArtistCreate, db: Session = Depends(get_db)):
    new_artist = Artist(
        full_name=artist.full_name,
        email=artist.email,
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
def get_all_artists(db: Session = Depends(get_db)):
    return db.query(Artist).all()

@router.get("/{artist_id}", response_model=ArtistResponse)
def get_artist(artist_id: str, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    return artist
