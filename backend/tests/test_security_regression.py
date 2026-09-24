import sys
from pathlib import Path

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
from app.models.impersonation_report import ImpersonationReport
from app.models.ownership_evidence import OwnershipEvidence
from app.utils.security import hash_password, verify_password, create_access_token, get_current_user

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestSecurityRegression(unittest.TestCase):
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

    def test_01_password_hashing_and_verification(self):
        plain_pw = "SuperSecretPass123!"
        hashed_pw = hash_password(plain_pw)
        
        self.assertNotEqual(plain_pw, hashed_pw)
        self.assertTrue(hashed_pw.startswith("$2b$"))
        self.assertTrue(verify_password(plain_pw, hashed_pw))
        self.assertFalse(verify_password("WrongPassword123!", hashed_pw))

    def test_02_jwt_generation_and_validation(self):
        artist_id = str(uuid.uuid4())
        token = create_access_token({"sub": artist_id, "role": "artist"})
        
        payload = get_current_user(token)
        self.assertEqual(payload["sub"], artist_id)
        self.assertEqual(payload["role"], "artist")

    def test_03_evidence_status_transition_rules(self):
        evidence = OwnershipEvidence(
            matched_artist_name="Test Artist",
            source_url="https://youtube.com/watch?v=abcdef12345",
            channel_confidence="high",
            evidence_type="structured_credit",
            match_type="exact",
            status="pending_review"
        )
        self.db.add(evidence)
        self.db.commit()

        # Pending -> Confirmed (Valid)
        evidence.status = "confirmed"
        evidence.reviewed_at = datetime.utcnow()
        self.db.commit()

        fetched = self.db.query(OwnershipEvidence).filter_by(id=evidence.id).first()
        self.assertEqual(fetched.status, "confirmed")
        self.assertIsNotNone(fetched.reviewed_at)

    def test_04_reviewer_attribution(self):
        admin_artist = Artist(
            id=uuid.uuid4(),
            full_name="Admin Reviewer",
            email="admin@example.com",
            role="admin"
        )
        self.db.add(admin_artist)
        self.db.commit()

        evidence = OwnershipEvidence(
            matched_artist_name="Credited Artist",
            source_url="https://youtube.com/watch?v=xyz98765",
            channel_confidence="medium",
            evidence_type="structured_credit",
            match_type="partial",
            status="pending_review"
        )
        self.db.add(evidence)
        self.db.commit()

        # Admin reviews evidence
        evidence.status = "confirmed"
        evidence.reviewed_at = datetime.utcnow()
        evidence.reviewed_by_user_id = admin_artist.id
        self.db.commit()

        fetched = self.db.query(OwnershipEvidence).filter_by(id=evidence.id).first()
        self.assertEqual(fetched.reviewed_by_user_id, admin_artist.id)

if __name__ == "__main__":
    unittest.main()
