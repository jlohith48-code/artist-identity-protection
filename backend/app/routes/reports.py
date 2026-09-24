from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ReportCreate
from app.utils.security import get_current_user_optional, require_admin
from app.services.report_service import ReportService
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

router = APIRouter(prefix="/reports", tags=["Impersonation Reports"])


class ReportCreateSchema(BaseModel):
    artist_id: uuid.UUID
    fake_profile_id: uuid.UUID
    evidence_summary: Optional[str] = None


class ReportResponse(BaseModel):
    id: uuid.UUID
    artist_id: uuid.UUID
    fake_profile_id: uuid.UUID
    status: str
    evidence_summary: Optional[str] = None
    submitted_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.post("/", response_model=ReportResponse)
def create_report(
    report: ReportCreateSchema,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    report_data = ReportCreate(
        artist_id=report.artist_id,
        fake_profile_id=report.fake_profile_id,
        evidence_summary=report.evidence_summary
    )
    return ReportService.create_report(db, report_data=report_data, current_user=current_user)


@router.get("/", response_model=List[ReportResponse])
def get_all_reports(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return ReportService.get_all_reports(db, skip=skip, limit=limit)


@router.get("/artist/{artist_id}", response_model=List[ReportResponse])
def get_reports_by_artist(artist_id: uuid.UUID, db: Session = Depends(get_db)):
    return ReportService.get_reports_by_artist(db, artist_id=artist_id)


@router.patch("/{report_id}/resolve", response_model=ReportResponse)
def resolve_report(
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    return ReportService.resolve_report(db, report_id=report_id, admin_user=admin_user)
