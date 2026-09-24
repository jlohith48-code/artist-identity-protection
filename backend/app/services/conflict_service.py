from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import logging

from app.models.ownership_conflict import OwnershipConflict
from app.models.ownership_evidence import OwnershipEvidence
from app.models.impersonation_report import ImpersonationReport
from app.models.song import Song

logger = logging.getLogger(__name__)

VALID_CONFLICT_STATUSES = {
    "detected",
    "pending_review",
    "under_review",
    "confirmed",
    "rejected",
    "resolved"
}

VALID_CONFLICT_TRANSITIONS = {
    "detected": {"pending_review", "under_review", "confirmed", "rejected", "resolved"},
    "pending_review": {"under_review", "confirmed", "rejected", "resolved"},
    "under_review": {"confirmed", "rejected", "resolved"},
    "confirmed": {"resolved"},
    "rejected": {"resolved"},
    "resolved": set()
}


class ConflictService:
    @staticmethod
    def get_conflicts(
        db: Session,
        status: Optional[str] = None,
        conflict_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[OwnershipConflict]:
        query = db.query(OwnershipConflict)
        if status:
            query = query.filter(OwnershipConflict.status == status)
        if conflict_type:
            query = query.filter(OwnershipConflict.conflict_type == conflict_type)
        return query.order_by(OwnershipConflict.flagged_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_conflict_by_id(db: Session, conflict_id: int) -> Optional[OwnershipConflict]:
        return db.query(OwnershipConflict).filter(OwnershipConflict.id == conflict_id).first()

    @staticmethod
    def create_or_update_similarity_conflict(
        db: Session,
        new_song_id: uuid.UUID,
        existing_song: Song,
        commit: bool = False
    ) -> OwnershipConflict:
        """
        Deduplicated conflict creation when a semantic similarity signal (>= 0.70) is detected between songs.
        """
        existing_conflict = db.query(OwnershipConflict).filter(
            OwnershipConflict.song_id == new_song_id,
            OwnershipConflict.conflict_type == "semantic_similarity"
        ).first()

        if existing_conflict:
            existing_conflict.flagged_at = datetime.utcnow()
            if commit:
                db.commit()
                db.refresh(existing_conflict)
            else:
                db.flush()
            return existing_conflict

        conflict = OwnershipConflict(
            song_id=new_song_id,
            claiming_profile_id=None,
            true_owner_artist_id=existing_song.artist_id,
            true_owner_claimed=True,
            conflict_type="semantic_similarity",
            evidence_id=None,
            status="pending_review",
            flagged_at=datetime.utcnow(),
            resolved=False
        )
        db.add(conflict)
        if commit:
            db.commit()
            db.refresh(conflict)
        else:
            db.flush()
        return conflict

    @staticmethod
    def create_or_update_evidence_conflict(
        db: Session,
        evidence: OwnershipEvidence,
        commit: bool = False
    ) -> OwnershipConflict:
        """
        Deduplicated conflict creation when external credit evidence is confirmed.
        """
        existing_conflict = db.query(OwnershipConflict).filter(
            OwnershipConflict.evidence_id == evidence.id,
            OwnershipConflict.conflict_type == "evidence_credit"
        ).first()

        if existing_conflict:
            existing_conflict.status = "pending_review" if evidence.status == "confirmed" else existing_conflict.status
            if commit:
                db.commit()
                db.refresh(existing_conflict)
            else:
                db.flush()
            return existing_conflict

        conflict = OwnershipConflict(
            song_id=None,
            claiming_profile_id=None,
            true_owner_artist_id=evidence.matched_artist_id,
            true_owner_claimed=True,
            conflict_type="evidence_credit",
            evidence_id=evidence.id,
            status="pending_review",
            flagged_at=datetime.utcnow(),
            resolved=False
        )
        db.add(conflict)
        if commit:
            db.commit()
            db.refresh(conflict)
        else:
            db.flush()
        return conflict

    @staticmethod
    def create_or_update_impersonation_conflict(
        db: Session,
        report: ImpersonationReport,
        commit: bool = False
    ) -> OwnershipConflict:
        """
        Deduplicated conflict creation when an artist files an impersonation report against a fake profile.
        """
        existing_conflict = db.query(OwnershipConflict).filter(
            OwnershipConflict.claiming_profile_id == report.fake_profile_id,
            OwnershipConflict.true_owner_artist_id == report.artist_id,
            OwnershipConflict.conflict_type == "impersonation_claim"
        ).first()

        if existing_conflict:
            existing_conflict.flagged_at = datetime.utcnow()
            if commit:
                db.commit()
                db.refresh(existing_conflict)
            else:
                db.flush()
            return existing_conflict

        conflict = OwnershipConflict(
            song_id=None,
            claiming_profile_id=report.fake_profile_id,
            true_owner_artist_id=report.artist_id,
            true_owner_claimed=True,
            conflict_type="impersonation_claim",
            evidence_id=None,
            status="pending_review",
            flagged_at=datetime.utcnow(),
            resolved=False
        )
        db.add(conflict)
        if commit:
            db.commit()
            db.refresh(conflict)
        else:
            db.flush()
        return conflict

    @staticmethod
    def update_conflict_status(
        db: Session,
        conflict: OwnershipConflict,
        new_status: str,
        reviewer_user_id: Optional[uuid.UUID] = None,
        commit: bool = True
    ) -> OwnershipConflict:
        if new_status not in VALID_CONFLICT_STATUSES:
            raise ValueError(f"Invalid conflict status '{new_status}'. Must be one of {VALID_CONFLICT_STATUSES}")

        allowed = VALID_CONFLICT_TRANSITIONS.get(conflict.status, set())
        if new_status not in allowed and new_status != conflict.status:
            raise ValueError(f"Invalid state transition from '{conflict.status}' to '{new_status}'")

        conflict.status = new_status
        conflict.reviewed_at = datetime.utcnow()
        if reviewer_user_id:
            conflict.reviewed_by_user_id = reviewer_user_id

        if new_status in {"resolved", "confirmed"}:
            conflict.resolved = True

        if commit:
            db.commit()
            db.refresh(conflict)
        else:
            db.flush()
        return conflict
