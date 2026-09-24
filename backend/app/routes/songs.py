from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database import get_db
from app.schemas import SongCreate, SongResponse
from app.utils.security import get_current_user_optional
from app.services.song_service import SongService
from app.services.similarity_service import find_similar_songs as find_similar_songs_service

router = APIRouter(prefix="/songs", tags=["Songs"])


@router.post("/")
def create_song(
    song: SongCreate,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    new_song, similarity_warning = SongService.create_song_atomic(db, song, current_user=current_user)
    response = SongResponse.model_validate(new_song).model_dump()
    response["similarity_warning"] = similarity_warning
    return response


@router.get("/", response_model=List[SongResponse])
def get_all_songs(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return SongService.get_all_songs(db, skip=skip, limit=limit)


@router.get("/artist/{artist_id}", response_model=List[SongResponse])
def get_songs_by_artist(artist_id: uuid.UUID, db: Session = Depends(get_db)):
    return SongService.get_songs_by_artist(db, artist_id=artist_id)


@router.get("/{song_id}", response_model=SongResponse)
def get_song(song_id: uuid.UUID, db: Session = Depends(get_db)):
    song = SongService.get_song_by_id(db, song_id=song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song


@router.get("/{song_id}/similar", response_model=List[dict])
def find_similar_songs(song_id: uuid.UUID, db: Session = Depends(get_db)):
    song = SongService.get_song_by_id(db, song_id=song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    try:
        return find_similar_songs_service(db, song_id, limit=20, min_threshold=0.50)
    except Exception:
        return []
