from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.database import get_db
from app.utils.security import get_current_user_optional, require_admin
from app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["Ownership Evidence"])

class EvidenceResponse(BaseModel):
    id: int
    matched_artist_id: Optional[uuid.UUID] = None
    matched_artist_name: str
    source_type: str
    source_url: str
    video_title: Optional[str] = None
    channel_id: Optional[str] = None
    channel_confidence: str
    evidence_type: str
    match_type: str
    role: Optional[str] = None
    raw_credit_text: Optional[str] = None
    stage_name_tag: Optional[str] = None
    status: str
    reviewed_at: Optional[datetime] = None
    reviewed_by_user_id: Optional[uuid.UUID] = None
    fetched_at: datetime

    class Config:
        from_attributes = True

class EvidenceStatusUpdate(BaseModel):
    status: str  # 'confirmed' | 'rejected' | 'pending_review'


@router.get("/pending", response_model=List[EvidenceResponse])
def get_pending_evidence(db: Session = Depends(get_db)):
    return EvidenceService.get_pending_evidence(db)


@router.get("/", response_model=List[EvidenceResponse])
def get_all_evidence(status: Optional[str] = None, db: Session = Depends(get_db)):
    return EvidenceService.get_all_evidence(db, status=status)


@router.patch("/{evidence_id}/status", response_model=EvidenceResponse)
def update_evidence_status(
    evidence_id: int,
    update: EvidenceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    return EvidenceService.update_evidence_status(
        db,
        evidence_id=evidence_id,
        new_status=update.status,
        current_user=current_user
    )
