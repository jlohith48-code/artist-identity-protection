from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date
import uuid

class ArtistCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    iprs_id: Optional[str] = None
    state: Optional[str] = None

class ArtistResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    phone: Optional[str] = None
    iprs_id: Optional[str] = None
    state: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SongCreate(BaseModel):
    artist_id: uuid.UUID
    title: str
    language: Optional[str] = None
    lyrics: str
    youtube_url: Optional[str] = None
    production_house: Optional[str] = None
    written_on: Optional[date] = None

class SongResponse(BaseModel):
    id: uuid.UUID
    artist_id: uuid.UUID
    title: str
    language: Optional[str] = None
    lyrics_hash: str
    lyrics_preview: Optional[str] = None
    youtube_url: Optional[str] = None
    production_house: Optional[str] = None
    written_on: Optional[date] = None
    registered_at: datetime

    class Config:
        from_attributes = True

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

class ConflictStatusUpdate(BaseModel):
    status: str  # 'pending_review' | 'under_review' | 'confirmed' | 'rejected' | 'resolved'

class ConflictResponse(BaseModel):
    id: int
    song_id: Optional[uuid.UUID] = None
    claiming_profile_id: Optional[uuid.UUID] = None
    true_owner_artist_id: Optional[uuid.UUID] = None
    true_owner_claimed: bool
    conflict_type: str
    evidence_id: Optional[int] = None
    status: str
    flagged_at: datetime
    resolved: bool
    reviewed_at: Optional[datetime] = None
    reviewed_by_user_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True
