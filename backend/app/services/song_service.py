from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid
import logging

from app.models.song import Song
from app.models.artist import Artist
from app.schemas import SongCreate
from app.utils.hashing import generate_lyrics_hash, generate_lyrics_preview
from app.utils.similarity import compute_lyrics_vector
from app.services.similarity_service import (
    store_song_embeddings,
    find_similar_songs as find_similar_songs_service
)
from app.services.conflict_service import ConflictService

logger = logging.getLogger(__name__)


class SongService:
    @staticmethod
    def create_song_atomic(
        db: Session,
        song_data: SongCreate,
        current_user: Optional[dict] = None
    ) -> Tuple[Song, Optional[str]]:
        """
        Atomic song creation, vector embedding storage, semantic similarity checking,
        and automatic OwnershipConflict creation when a high similarity signal is detected.
        """
        # IDOR check: caller must own artist_id unless admin
        if current_user:
            user_role = current_user.get("role", "artist")
            user_artist_id = current_user.get("sub")
            if user_role != "admin" and str(song_data.artist_id) != str(user_artist_id):
                raise HTTPException(
                    status_code=403,
                    detail="Forbidden: You can only file songs for your own artist identity."
                )

        artist = db.query(Artist).filter(Artist.id == song_data.artist_id).first()
        if not artist:
            raise HTTPException(status_code=404, detail="Artist not found. Register the artist first.")

        # 1. SHA-256 Exact Duplicate Check
        lyrics_hash = generate_lyrics_hash(song_data.lyrics)
        existing = db.query(Song).filter(Song.lyrics_hash == lyrics_hash).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"These exact lyrics are already registered under song '{existing.title}' (registered {existing.registered_at})"
            )

        new_vector = compute_lyrics_vector(song_data.lyrics)

        new_song = Song(
            artist_id=song_data.artist_id,
            title=song_data.title,
            language=song_data.language,
            lyrics_hash=lyrics_hash,
            lyrics_preview=generate_lyrics_preview(song_data.lyrics),
            lyrics_vector=new_vector,
            youtube_url=song_data.youtube_url,
            production_house=song_data.production_house,
            written_on=song_data.written_on,
        )

        try:
            db.add(new_song)
            db.flush()

            # 2. Vector Embedding Persistence
            store_song_embeddings(db, new_song.id, song_data.lyrics, commit=False)

            # 3. Semantic Similarity Search against existing database
            similar = find_similar_songs_service(db, new_song.id, limit=5, min_threshold=0.70)
            similarity_warning = None
            if similar:
                top_match = similar[0]
                similarity_warning = (
                    f"{round(top_match['similarity_score']*100, 1)}% semantic similarity to song '{top_match['title']}' "
                    f"(Match level: {top_match['match_level']}). Possible paraphrase or partial reuse - flagged for review."
                )

                # Connect Similarity to OwnershipConflict if top match belongs to a different artist
                matched_song_id = uuid.UUID(top_match["song_id"])
                matched_song = db.query(Song).filter(Song.id == matched_song_id).first()
                if matched_song and str(matched_song.artist_id) != str(new_song.artist_id):
                    ConflictService.create_or_update_similarity_conflict(
                        db,
                        new_song_id=new_song.id,
                        existing_song=matched_song,
                        commit=False
                    )

            db.commit()
            db.refresh(new_song)
            return new_song, similarity_warning

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create song and embeddings atomically: {str(e)}"
            )

    @staticmethod
    def get_song_by_id(db: Session, song_id: uuid.UUID) -> Optional[Song]:
        return db.query(Song).filter(Song.id == song_id).first()

    @staticmethod
    def get_songs_by_artist(db: Session, artist_id: uuid.UUID) -> List[Song]:
        return db.query(Song).filter(Song.artist_id == artist_id).all()

    @staticmethod
    def get_all_songs(db: Session, skip: int = 0, limit: int = 100) -> List[Song]:
        return db.query(Song).offset(skip).limit(limit).all()
