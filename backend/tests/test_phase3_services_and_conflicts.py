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
from app.models.artist_profile import ArtistProfile
from app.models.song import Song
from app.models.ownership_evidence import OwnershipEvidence
from app.models.ownership_conflict import OwnershipConflict
from app.models.impersonation_report import ImpersonationReport
from app.schemas import SongCreate, ReportCreate
from app.services.song_service import SongService
from app.services.evidence_service import EvidenceService
from app.services.conflict_service import ConflictService
from app.services.report_service import ReportService
from app.services.similarity_service import store_song_embeddings

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestPhase3ServicesAndConflicts(unittest.TestCase):
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

    def test_01_conflict_service_lifecycle_and_state_machine(self):
        artist = Artist(full_name="Conflict Owner Artist", email="conflictowner@example.com")
        admin = Artist(full_name="Reviewer Admin", email="revieweradmin@example.com", role="admin")
        self.db.add_all([artist, admin])
        self.db.commit()

        song = Song(
            artist_id=artist.id,
            title="Conflicting Song Title",
            lyrics_hash="hash_conflict_test",
            lyrics_preview="Lyrics test"
        )
        self.db.add(song)
        self.db.commit()

        # Create similarity conflict
        conflict = ConflictService.create_or_update_similarity_conflict(
            self.db,
            new_song_id=song.id,
            existing_song=song,
            commit=True
        )

        self.assertIsNotNone(conflict.id)
        self.assertEqual(conflict.status, "pending_review")
        self.assertFalse(conflict.resolved)

        # Transition state: pending_review -> under_review
        updated = ConflictService.update_conflict_status(
            self.db,
            conflict=conflict,
            new_status="under_review",
            reviewer_user_id=admin.id,
            commit=True
        )
        self.assertEqual(updated.status, "under_review")
        self.assertEqual(updated.reviewed_by_user_id, admin.id)
        self.assertIsNotNone(updated.reviewed_at)

        # Transition state: under_review -> resolved
        resolved_conflict = ConflictService.update_conflict_status(
            self.db,
            conflict=conflict,
            new_status="resolved",
            reviewer_user_id=admin.id,
            commit=True
        )
        self.assertEqual(resolved_conflict.status, "resolved")
        self.assertTrue(resolved_conflict.resolved)

        # Verify invalid state transition raises ValueError
        with self.assertRaises(ValueError):
            ConflictService.update_conflict_status(
                self.db,
                conflict=resolved_conflict,
                new_status="pending_review",
                commit=False
            )

    def test_02_similarity_signal_creates_conflict(self):
        artist1 = Artist(full_name="Artist One", email="artist1@example.com")
        artist2 = Artist(full_name="Artist Two", email="artist2@example.com")
        self.db.add_all([artist1, artist2])
        self.db.commit()

        # Register original song by Artist 1
        s1_data = SongCreate(
            artist_id=artist1.id,
            title="Original Sunset Song",
            lyrics="The sun sets over the ocean blue, stars shine bright in the evening sky tonight."
        )
        s1, _ = SongService.create_song_atomic(self.db, s1_data)

        # Register paraphrased song by Artist 2 (triggers similarity signal >= 0.70)
        s2_data = SongCreate(
            artist_id=artist2.id,
            title="Paraphrased Sunset Song",
            lyrics="The evening sun sinks down into the blue sea while stars glow bright high above tonight."
        )

        # Ensure embeddings can be generated cleanly
        store_song_embeddings(self.db, s1.id, s1_data.lyrics, model_name="all-MiniLM-L6-v2")

        with patch("app.services.similarity_service.DEFAULT_MODEL_NAME", "all-MiniLM-L6-v2"):
            s2, warning = SongService.create_song_atomic(self.db, s2_data)

        self.assertIsNotNone(s2)

        # Verify an OwnershipConflict was automatically created linking s2 to artist1
        conflicts = self.db.query(OwnershipConflict).filter(OwnershipConflict.song_id == s2.id).all()
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, "semantic_similarity")
        self.assertEqual(conflicts[0].true_owner_artist_id, artist1.id)
        self.assertEqual(conflicts[0].status, "pending_review")

    def test_03_evidence_confirmation_creates_conflict(self):
        artist = Artist(full_name="Evidence Artist", email="evidenceartist@example.com")
        admin = Artist(full_name="Evidence Admin", email="evidenceadmin@example.com", role="admin")
        self.db.add_all([artist, admin])
        self.db.commit()

        evidence = OwnershipEvidence(
            matched_artist_id=artist.id,
            matched_artist_name="Evidence Artist",
            source_url="https://youtube.com/watch?v=99999",
            channel_confidence="high",
            evidence_type="structured_credit",
            match_type="exact",
            status="pending_review"
        )
        self.db.add(evidence)
        self.db.commit()

        # Admin confirms evidence
        user_ctx = {"sub": str(admin.id), "role": "admin"}
        updated_evidence = EvidenceService.update_evidence_status(
            self.db,
            evidence_id=evidence.id,
            new_status="confirmed",
            current_user=user_ctx
        )

        self.assertEqual(updated_evidence.status, "confirmed")
        self.assertEqual(updated_evidence.reviewed_by_user_id, admin.id)

        # Verify connected OwnershipConflict created
        conflict = self.db.query(OwnershipConflict).filter(OwnershipConflict.evidence_id == evidence.id).first()
        self.assertIsNotNone(conflict)
        self.assertEqual(conflict.conflict_type, "evidence_credit")
        self.assertEqual(conflict.true_owner_artist_id, artist.id)

        # Confirming evidence again (or updating status) should deduplicate and update existing conflict
        EvidenceService.update_evidence_status(self.db, evidence.id, "confirmed", current_user=user_ctx)
        conflict_count = self.db.query(OwnershipConflict).filter(OwnershipConflict.evidence_id == evidence.id).count()
        self.assertEqual(conflict_count, 1)

    def test_04_impersonation_report_creates_and_resolves_conflict(self):
        artist = Artist(full_name="Impersonated Artist", email="impersonated@example.com")
        admin = Artist(full_name="Report Admin", email="reportadmin@example.com", role="admin")
        self.db.add_all([artist, admin])
        self.db.commit()

        fake_profile = ArtistProfile(
            artist_id=artist.id,
            platform="Spotify",
            claimed_display_name="Impersonator Fake Profile"
        )
        self.db.add(fake_profile)
        self.db.commit()

        report_data = ReportCreate(
            artist_id=artist.id,
            fake_profile_id=fake_profile.id,
            evidence_summary="Fake profile stealing streaming royalties"
        )

        user_ctx = {"sub": str(artist.id), "role": "artist"}
        report = ReportService.create_report(self.db, report_data, current_user=user_ctx)

        self.assertIsNotNone(report.id)
        self.assertEqual(report.status, "pending")

        # Verify linked OwnershipConflict created
        conflict = self.db.query(OwnershipConflict).filter(
            OwnershipConflict.claiming_profile_id == fake_profile.id,
            OwnershipConflict.conflict_type == "impersonation_claim"
        ).first()
        self.assertIsNotNone(conflict)
        self.assertEqual(conflict.status, "pending_review")

        # Resolve report via ReportService
        admin_ctx = {"sub": str(admin.id), "role": "admin"}
        resolved_report = ReportService.resolve_report(self.db, report.id, admin_user=admin_ctx)
        self.assertEqual(resolved_report.status, "resolved")

        # Verify linked conflict also marked resolved
        self.db.refresh(conflict)
        self.assertEqual(conflict.status, "resolved")
        self.assertTrue(conflict.resolved)


if __name__ == "__main__":
    unittest.main()
