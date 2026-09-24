from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
import uuid
import logging

from app.models.ownership_evidence import OwnershipEvidence
from app.services.conflict_service import ConflictService

logger = logging.getLogger(__name__)

VALID_EVIDENCE_STATUSES = {"confirmed", "rejected", "pending_review", "auto_confirmed"}
VALID_EVIDENCE_TRANSITIONS = {
    "pending_review": {"confirmed", "rejected"},
    "auto_confirmed": {"confirmed", "rejected"},
    "confirmed": set(),
    "rejected": set()
}


class EvidenceService:
    @staticmethod
    def get_pending_evidence(db: Session) -> List[OwnershipEvidence]:
        return db.query(OwnershipEvidence).filter(
            OwnershipEvidence.status == "pending_review"
        ).order_by(OwnershipEvidence.fetched_at.desc()).all()

    @staticmethod
    def get_all_evidence(db: Session, status: Optional[str] = None) -> List[OwnershipEvidence]:
        query = db.query(OwnershipEvidence)
        if status:
            if status not in VALID_EVIDENCE_STATUSES:
                raise HTTPException(status_code=400, detail=f"Invalid status parameter. Must be one of {VALID_EVIDENCE_STATUSES}")
            query = query.filter(OwnershipEvidence.status == status)
        return query.order_by(OwnershipEvidence.fetched_at.desc()).all()

    @staticmethod
    def update_evidence_status(
        db: Session,
        evidence_id: int,
        new_status: str,
        current_user: Optional[dict] = None
    ) -> OwnershipEvidence:
        if new_status not in VALID_EVIDENCE_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {VALID_EVIDENCE_STATUSES}")

        evidence = db.query(OwnershipEvidence).filter(OwnershipEvidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence record not found")

        allowed_next = VALID_EVIDENCE_TRANSITIONS.get(evidence.status, set())
        if new_status not in allowed_next and new_status != evidence.status:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition from '{evidence.status}' to '{new_status}'"
            )

        evidence.status = new_status
        evidence.reviewed_at = datetime.utcnow()
        if current_user and "sub" in current_user:
            try:
                evidence.reviewed_by_user_id = uuid.UUID(current_user["sub"])
            except (ValueError, TypeError):
                pass

        # If evidence is confirmed, automatically link/create OwnershipConflict
        if new_status == "confirmed":
            ConflictService.create_or_update_evidence_conflict(db, evidence, commit=False)

        db.commit()
        db.refresh(evidence)
        return evidence
