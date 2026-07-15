from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.song import Song
from app.models.artist import Artist
from app.schemas import SongCreate, SongResponse
from app.utils.hashing import generate_lyrics_hash, generate_lyrics_preview
from app.utils.similarity import compute_lyrics_vector, cosine_similarity_from_json
from typing import List
import uuid

router = APIRouter(prefix="/songs", tags=["Songs"])

SIMILARITY_THRESHOLD = 0.85

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

    new_vector = compute_lyrics_vector(song.lyrics)

    all_songs = db.query(Song).filter(Song.lyrics_vector.isnot(None)).all()
    best_match = None
    best_score = 0.0
    for other in all_songs:
        score = cosine_similarity_from_json(new_vector, other.lyrics_vector)
        if score > best_score:
            best_score = score
            best_match = other

    similarity_warning = None
    if best_match and best_score >= SIMILARITY_THRESHOLD:
        similarity_warning = (
            f"Warning: {round(best_score*100,1)}% similar to song '{best_match.title}' "
            f"(registered {best_match.registered_at}). Possible paraphrase or partial reuse - flagged for review."
        )

    new_song = Song(
        artist_id=song.artist_id,
        title=song.title,
        language=song.language,
        lyrics_hash=lyrics_hash,
        lyrics_preview=generate_lyrics_preview(song.lyrics),
        lyrics_vector=new_vector,
        youtube_url=song.youtube_url,
        production_house=song.production_house,
        written_on=song.written_on,
    )
    db.add(new_song)
    db.commit()
    db.refresh(new_song)

    response = SongResponse.model_validate(new_song)
    if similarity_warning:
        print(f"SIMILARITY ALERT: {similarity_warning}")

    return response

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

@router.get("/{song_id}/similar", response_model=List[dict])
def find_similar_songs(song_id: uuid.UUID, db: Session = Depends(get_db)):
    target = db.query(Song).filter(Song.id == song_id).first()
    if not target or not target.lyrics_vector:
        raise HTTPException(status_code=404, detail="Song not found or has no vector")

    all_songs = db.query(Song).filter(Song.id != song_id, Song.lyrics_vector.isnot(None)).all()
    results = []
    for other in all_songs:
        score = cosine_similarity_from_json(target.lyrics_vector, other.lyrics_vector)
        if score >= 0.5:
            results.append({
                "song_id": str(other.id),
                "title": other.title,
                "artist_id": str(other.artist_id),
                "similarity_score": round(score, 3)
            })
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results
