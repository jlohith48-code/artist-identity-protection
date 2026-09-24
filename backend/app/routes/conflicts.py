from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.database import get_db
from app.schemas import ConflictResponse, ConflictStatusUpdate
from app.services.conflict_service import ConflictService
from app.utils.security import require_admin, get_current_user_optional

router = APIRouter(prefix="/conflicts", tags=["Ownership Conflicts"])


@router.get("/", response_model=List[ConflictResponse])
def get_all_conflicts(
    status: Optional[str] = Query(None, description="Filter by conflict status"),
    conflict_type: Optional[str] = Query(None, description="Filter by conflict type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return ConflictService.get_conflicts(db, status=status, conflict_type=conflict_type, skip=skip, limit=limit)


@router.get("/{conflict_id}", response_model=ConflictResponse)
def get_conflict(
    conflict_id: int,
    db: Session = Depends(get_db)
):
    conflict = ConflictService.get_conflict_by_id(db, conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Ownership conflict not found")
    return conflict


@router.patch("/{conflict_id}/status", response_model=ConflictResponse)
def update_conflict_status(
    conflict_id: int,
    update: ConflictStatusUpdate,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    conflict = ConflictService.get_conflict_by_id(db, conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Ownership conflict not found")

    reviewer_id = None
    if admin_user and "sub" in admin_user:
        try:
            reviewer_id = uuid.UUID(admin_user["sub"])
        except (ValueError, TypeError):
            pass

    try:
        return ConflictService.update_conflict_status(
            db,
            conflict=conflict,
            new_status=update.status,
            reviewer_user_id=reviewer_id,
            commit=True
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{conflict_id}/resolve", response_model=ConflictResponse)
def resolve_conflict(
    conflict_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    conflict = ConflictService.get_conflict_by_id(db, conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Ownership conflict not found")

    reviewer_id = None
    if admin_user and "sub" in admin_user:
        try:
            reviewer_id = uuid.UUID(admin_user["sub"])
        except (ValueError, TypeError):
            pass

    try:
        return ConflictService.update_conflict_status(
            db,
            conflict=conflict,
            new_status="resolved",
            reviewer_user_id=reviewer_id,
            commit=True
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
