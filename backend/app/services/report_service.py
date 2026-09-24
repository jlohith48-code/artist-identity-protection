from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
import uuid
import logging

from app.models.impersonation_report import ImpersonationReport
from app.models.artist import Artist
from app.models.artist_profile import ArtistProfile
from app.schemas import ReportCreate
from app.services.conflict_service import ConflictService

logger = logging.getLogger(__name__)


class ReportService:
    @staticmethod
    def create_report(
        db: Session,
        report_data: ReportCreate,
        current_user: Optional[dict] = None
    ) -> ImpersonationReport:
        if current_user:
            user_role = current_user.get("role", "artist")
            user_artist_id = current_user.get("sub")
            if user_role != "admin" and str(report_data.artist_id) != str(user_artist_id):
                raise HTTPException(
                    status_code=403,
                    detail="Forbidden: You can only file reports for your own artist identity."
                )

        artist = db.query(Artist).filter(Artist.id == report_data.artist_id).first()
        if not artist:
            raise HTTPException(status_code=404, detail="Artist not found")

        fake_profile = db.query(ArtistProfile).filter(ArtistProfile.id == report_data.fake_profile_id).first()
        if not fake_profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        new_report = ImpersonationReport(
            artist_id=report_data.artist_id,
            fake_profile_id=report_data.fake_profile_id,
            evidence_summary=report_data.evidence_summary,
            status="pending",
        )
        db.add(new_report)
        db.flush()

        # Connect ImpersonationReport to OwnershipConflict domain
        ConflictService.create_or_update_impersonation_conflict(db, new_report, commit=False)

        db.commit()
        db.refresh(new_report)
        return new_report

    @staticmethod
    def get_all_reports(db: Session, skip: int = 0, limit: int = 100) -> List[ImpersonationReport]:
        return db.query(ImpersonationReport).order_by(ImpersonationReport.submitted_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_reports_by_artist(db: Session, artist_id: uuid.UUID) -> List[ImpersonationReport]:
        return db.query(ImpersonationReport).filter(ImpersonationReport.artist_id == artist_id).all()

    @staticmethod
    def resolve_report(
        db: Session,
        report_id: uuid.UUID,
        admin_user: Optional[dict] = None
    ) -> ImpersonationReport:
        report = db.query(ImpersonationReport).filter(ImpersonationReport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        report.status = "resolved"
        report.resolved_at = datetime.utcnow()

        # Resolve linked OwnershipConflict if present
        reviewer_id = None
        if admin_user and "sub" in admin_user:
            try:
                reviewer_id = uuid.UUID(admin_user["sub"])
            except (ValueError, TypeError):
                pass

        existing_conflict = db.query(ConflictService.create_or_update_impersonation_conflict.__globals__["OwnershipConflict"]).filter(
            ConflictService.create_or_update_impersonation_conflict.__globals__["OwnershipConflict"].claiming_profile_id == report.fake_profile_id,
            ConflictService.create_or_update_impersonation_conflict.__globals__["OwnershipConflict"].true_owner_artist_id == report.artist_id,
            ConflictService.create_or_update_impersonation_conflict.__globals__["OwnershipConflict"].conflict_type == "impersonation_claim"
        ).first()

        if existing_conflict:
            ConflictService.update_conflict_status(db, existing_conflict, new_status="resolved", reviewer_user_id=reviewer_id, commit=False)

        db.commit()
        db.refresh(report)
        return report
