import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
import uuid
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.artist import Artist
from app.models.song import Song
from app.models.artist_profile import ArtistProfile
from app.models.ownership_evidence import OwnershipEvidence
from app.models.impersonation_report import ImpersonationReport
from app.utils.hashing import generate_lyrics_hash, generate_lyrics_preview
from app.utils.similarity import compute_lyrics_vector, cosine_similarity_from_json
from app.utils.feature_calc import name_similarity, compute_profile_features
from app.utils.security import hash_password, verify_password, create_access_token, get_current_user

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestCoreModules(unittest.TestCase):
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

    def test_01_hashing_and_preview(self):
        text = "   This is a SAMPLE lyric text with UPPERCASE and   extra   spaces.  "
        h1 = generate_lyrics_hash(text)
        h2 = generate_lyrics_hash("this is a sample lyric text with uppercase and extra spaces.")
        self.assertEqual(h1, h2)
        
        preview = generate_lyrics_preview(text, word_limit=3)
        self.assertTrue(preview.startswith("This is a"))

    def test_02_vector_similarity(self):
        lyric1 = "Walk under the bright midnight stars and moon."
        lyric2 = "Walking under bright midnight stars and moon light."
        vec1 = compute_lyrics_vector(lyric1)
        vec2 = compute_lyrics_vector(lyric2)
        
        score = cosine_similarity_from_json(vec1, vec2)
        self.assertGreater(score, 0.5)

    def test_03_security_passwords_and_tokens(self):
        plain = "mysecretpassword123"
        hashed = hash_password(plain)
        self.assertTrue(verify_password(plain, hashed))
        self.assertFalse(verify_password("wrongpassword", hashed))

        token = create_access_token({"sub": "artist_123", "role": "artist"})
        self.assertIsInstance(token, str)

    def test_04_feature_calc(self):
        artist = Artist(
            id=uuid.uuid4(),
            full_name="Chandrabose",
            email="chandrabose@example.com"
        )
        self.db.add(artist)
        self.db.commit()

        profile = ArtistProfile(
            id=uuid.uuid4(),
            artist_id=artist.id,
            platform="Spotify",
            claimed_display_name="Chandrabose Official",
            monthly_listeners=50000,
            follower_count=100,
            total_songs=10,
            account_created_date=date(2026, 1, 1)
        )
        self.db.add(profile)
        self.db.commit()

        features = compute_profile_features("Chandrabose", profile, self.db)
        self.assertIn("name_similarity_score", features)
        self.assertIn("growth_velocity_score", features)
        self.assertGreaterEqual(features["name_similarity_score"], 0.7)

    def test_05_evidence_model_and_attribution(self):
        admin = Artist(
            id=uuid.uuid4(),
            full_name="Admin Reviewer",
            email="admin_review@example.com",
            role="admin"
        )
        self.db.add(admin)
        self.db.commit()

        evidence = OwnershipEvidence(
            matched_artist_name="Test Artist",
            source_url="https://youtube.com/watch?v=12345",
            channel_confidence="high",
            evidence_type="structured_credit",
            match_type="exact",
            status="pending_review"
        )
        self.db.add(evidence)
        self.db.commit()

        evidence.status = "confirmed"
        evidence.reviewed_at = datetime.utcnow()
        evidence.reviewed_by_user_id = admin.id
        self.db.commit()

        fetched = self.db.query(OwnershipEvidence).filter_by(id=evidence.id).first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.status, "confirmed")
        self.assertEqual(fetched.reviewed_by_user_id, admin.id)

if __name__ == "__main__":
    unittest.main()
