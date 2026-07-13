from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.song import Song
from app.models.artist import Artist
from app.schemas import SongCreate, SongResponse
from app.utils.hashing import generate_lyrics_hash, generate_lyrics_preview
from typing import List
import uuid

router = APIRouter(prefix="/songs", tags=["Songs"])

@router.post("/", response_model=SongResponse)
def create_song(song: SongCreate, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == song.artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found. Register the artist first.")

    lyrics_hash = generate_lyrics_hash(song.lyrics)

    existing = db.query(Song).filter(Song.lyrics_hash == lyrics_hash).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"These exact lyrics are already registered under song '{existing.title}' (registered {existing.registered_at})"
        )

    new_song = Song(
        artist_id=song.artist_id,
        title=song.title,
        language=song.language,
        lyrics_hash=lyrics_hash,
        lyrics_preview=generate_lyrics_preview(song.lyrics),
        youtube_url=song.youtube_url,
        production_house=song.production_house,
        written_on=song.written_on,
    )
    db.add(new_song)
    db.commit()
    db.refresh(new_song)
    return new_song

@router.get("/", response_model=List[SongResponse])
def get_all_songs(db: Session = Depends(get_db)):
    return db.query(Song).all()

@router.get("/artist/{artist_id}", response_model=List[SongResponse])
def get_songs_by_artist(artist_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(Song).filter(Song.artist_id == artist_id).all()

@router.get("/{song_id}", response_model=SongResponse)
def get_song(song_id: uuid.UUID, db: Session = Depends(get_db)):
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song
