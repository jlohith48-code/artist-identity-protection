from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.impersonation_report import ImpersonationReport
from app.models.artist import Artist
from app.models.artist_profile import ArtistProfile
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

router = APIRouter(prefix="/reports", tags=["Impersonation Reports"])

class ReportCreate(BaseModel):
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
def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == report.artist_id).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    fake_profile = db.query(ArtistProfile).filter(ArtistProfile.id == report.fake_profile_id).first()
    if not fake_profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    new_report = ImpersonationReport(
        artist_id=report.artist_id,
        fake_profile_id=report.fake_profile_id,
        evidence_summary=report.evidence_summary,
        status="pending",
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

@router.get("/", response_model=List[ReportResponse])
def get_all_reports(db: Session = Depends(get_db)):
    return db.query(ImpersonationReport).order_by(ImpersonationReport.submitted_at.desc()).all()

@router.get("/artist/{artist_id}", response_model=List[ReportResponse])
def get_reports_by_artist(artist_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(ImpersonationReport).filter(ImpersonationReport.artist_id == artist_id).all()

@router.patch("/{report_id}/resolve", response_model=ReportResponse)
def resolve_report(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = db.query(ImpersonationReport).filter(ImpersonationReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = "resolved"
    report.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(report)
    return report
