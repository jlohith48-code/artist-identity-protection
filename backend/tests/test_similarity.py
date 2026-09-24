import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.artist import Artist
from app.models.song import Song
from app.models.song_embedding import SongEmbedding
from app.services.similarity_service import (
    normalize_lyrics,
    chunk_lyrics,
    store_song_embeddings,
    find_similar_songs,
    classify_similarity_level
)
from app.ml.backfill_embeddings import backfill_song_embeddings

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestSimilarityService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)

    def setUp(self):
        self.db = TestingSessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_normalize_lyrics(self):
        raw_text = "  Hello  World! \n This IS   A test. "
        normalized = normalize_lyrics(raw_text)
        self.assertIn("hello world", normalized)
        self.assertIn("this is a test", normalized)
        self.assertNotIn("!", normalized)

    def test_02_chunk_lyrics(self):
        single_stanza = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        chunks = chunk_lyrics(single_stanza)
        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(chunks[0], normalize_lyrics(single_stanza))

        multi_stanza = "Verse 1 Line 1\nVerse 1 Line 2\n\nChorus Line 1\nChorus Line 2"
        stanza_chunks = chunk_lyrics(multi_stanza)
        self.assertEqual(len(stanza_chunks), 3)

    def test_03_classify_similarity_level(self):
        self.assertEqual(classify_similarity_level(0.98), "likely_duplicate")
        self.assertEqual(classify_similarity_level(0.85), "high_similarity")
        self.assertEqual(classify_similarity_level(0.70), "possible_similarity")
        self.assertEqual(classify_similarity_level(0.40), "low_similarity")

    def test_04_embedding_storage_and_search(self):
        artist = Artist(full_name="Vector Test Artist", email="vectortest@example.com")
        self.db.add(artist)
        self.db.commit()

        s1 = Song(
            artist_id=artist.id,
            title="Original Sunset",
            language="English",
            lyrics_hash="hash_s1",
            lyrics_preview="The sun sets over the ocean blue, stars shine bright in the evening sky.",
            lyrics_vector=None
        )
        s2 = Song(
            artist_id=artist.id,
            title="Paraphrased Sunset",
            language="English",
            lyrics_hash="hash_s2",
            lyrics_preview="The evening sun sinks down into the blue sea while stars glow bright high above.",
            lyrics_vector=None
        )
        s3 = Song(
            artist_id=artist.id,
            title="Unrelated Song",
            language="English",
            lyrics_hash="hash_s3",
            lyrics_preview="PostgreSQL pgvector provides HNSW index structures for vector distance operations.",
            lyrics_vector=None
        )
        self.db.add_all([s1, s2, s3])
        self.db.commit()

        lyrics1 = "The sun sets over the ocean blue, stars shine bright in the evening sky."
        lyrics2 = "The evening sun sinks down into the blue sea while stars glow bright high above."
        lyrics3 = "PostgreSQL pgvector provides HNSW index structures for vector distance operations."

        store_song_embeddings(self.db, s1.id, lyrics1, model_name="all-MiniLM-L6-v2")
        store_song_embeddings(self.db, s2.id, lyrics2, model_name="all-MiniLM-L6-v2")
        store_song_embeddings(self.db, s3.id, lyrics3, model_name="all-MiniLM-L6-v2")

        # Search similar songs to s1
        results = find_similar_songs(self.db, s1.id, limit=5, min_threshold=0.3)

        self.assertGreaterEqual(len(results), 1)
        top_result = results[0]
        self.assertEqual(top_result["song_id"], str(s2.id))
        self.assertGreater(top_result["similarity_score"], 0.60)

    def test_05_backfill_embeddings_idempotence(self):
        artist = Artist(full_name="Backfill Test Artist", email="backfilltest@example.com")
        self.db.add(artist)
        self.db.commit()

        song = Song(
            artist_id=artist.id,
            title="Backfill Song",
            language="English",
            lyrics_hash="hash_backfill",
            lyrics_preview="Testing backfill script idempotency and database records generation.",
            lyrics_vector=None
        )
        self.db.add(song)
        self.db.commit()

        processed, skipped = backfill_song_embeddings(self.db, force=False, model_name="all-MiniLM-L6-v2")
        self.assertEqual(processed, 1)

        # Second run without force should skip
        processed_2, skipped_2 = backfill_song_embeddings(self.db, force=False, model_name="all-MiniLM-L6-v2")
        self.assertEqual(processed_2, 0)
        self.assertGreaterEqual(skipped_2, 1)

    def test_06_finding_03_missing_embeddings_handling(self):
        """
        Regression Test for FINDING-03:
        Verifies that querying similarity for a song with missing embeddings or no lyrics_preview
        does NOT crash with AttributeError or 500 error, and safely returns an empty result list.
        """
        artist = Artist(full_name="No Embedding Artist", email="noembedding@example.com")
        self.db.add(artist)
        self.db.commit()

        # Song with no embeddings generated and lyrics_preview only
        song_no_emb = Song(
            artist_id=artist.id,
            title="Song Without Embeddings",
            language="English",
            lyrics_hash="hash_no_emb",
            lyrics_preview=None,  # No lyrics text
            lyrics_vector=None
        )
        self.db.add(song_no_emb)
        self.db.commit()

        # Query similarity on song without embeddings/lyrics
        results = find_similar_songs(self.db, song_no_emb.id, limit=5, min_threshold=0.5)
        self.assertEqual(results, [])  # Should safely return empty list without crash

    def test_07_finding_02_atomic_transaction_rollback(self):
        """
        Regression Test for FINDING-02:
        Verifies that if embedding generation fails during song creation,
        the transaction rolls back and NO song or partial embedding record remains in DB.
        """
        artist = Artist(full_name="Atomic Test Artist", email="atomictest@example.com")
        self.db.add(artist)
        self.db.commit()

        song_id = uuid.uuid4()
        new_song = Song(
            id=song_id,
            artist_id=artist.id,
            title="Failed Embedding Song",
            language="English",
            lyrics_hash="hash_failed_emb",
            lyrics_preview="Lyrics that will fail embedding calculation...",
            lyrics_vector=None
        )

        # Simulate transaction block failure during store_song_embeddings
        try:
            self.db.add(new_song)
            self.db.flush()

            # Mock failure during embedding generation
            with patch("app.services.similarity_service.compute_vector", side_effect=RuntimeError("PyTorch GPU OOM")):
                store_song_embeddings(self.db, new_song.id, "Some lyrics", commit=False)

            self.db.commit()
        except RuntimeError:
            self.db.rollback()

        # Verify song was NOT saved in database
        fetched_song = self.db.query(Song).filter(Song.id == song_id).first()
        self.assertIsNone(fetched_song, "Song must be rolled back if embedding generation fails!")

        # Verify no partial embeddings exist
        fetched_embeddings = self.db.query(SongEmbedding).filter(SongEmbedding.song_id == song_id).all()
        self.assertEqual(len(fetched_embeddings), 0, "No partial embeddings must remain after rollback!")


if __name__ == "__main__":
    unittest.main()
