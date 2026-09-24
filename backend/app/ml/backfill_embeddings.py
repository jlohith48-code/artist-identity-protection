import sys
import os
import argparse
import logging
from sqlalchemy.orm import Session

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import SessionLocal
from app.models.song import Song
from app.models.song_embedding import SongEmbedding
from app.services.similarity_service import store_song_embeddings, DEFAULT_MODEL_NAME

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def backfill_song_embeddings(db: Session, force: bool = False, model_name: str = DEFAULT_MODEL_NAME):
    """
    Idempotent script to generate embeddings for all songs currently missing entries in song_embeddings.
    If force=True, re-generates embeddings for all songs.
    """
    songs = db.query(Song).all()
    logger.info(f"Starting embedding backfill for {len(songs)} songs using model '{model_name}'...")

    processed_count = 0
    skipped_count = 0

    for song in songs:
        lyrics_text = getattr(song, 'lyrics', None) or getattr(song, 'lyrics_preview', None)
        if not lyrics_text:
            logger.warning(f"Song {song.id} ('{song.title}') has no lyrics text. Skipping.")
            skipped_count += 1
            continue

        existing_embeddings = db.query(SongEmbedding).filter(SongEmbedding.song_id == song.id).count()

        if existing_embeddings > 0 and not force:
            logger.debug(f"Song {song.id} ('{song.title}') already has {existing_embeddings} embeddings. Skipping.")
            skipped_count += 1
            continue

        try:
            records = store_song_embeddings(db, song.id, lyrics_text, model_name=model_name)
            processed_count += 1
            logger.info(f"Backfilled song {song.id} ('{song.title}'): created {len(records)} embedding chunks.")
        except Exception as e:
            logger.error(f"Failed to process song {song.id} ('{song.title}'): {str(e)}")

    logger.info(f"Backfill complete! Processed: {processed_count}, Skipped: {skipped_count}.")
    return processed_count, skipped_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill vector embeddings for existing songs.")
    parser.add_argument("--force", action="store_true", help="Force re-generation of embeddings even if already existing.")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_NAME, help="Model name to use for embeddings.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        backfill_song_embeddings(db, force=args.force, model_name=args.model)
    finally:
        db.close()
