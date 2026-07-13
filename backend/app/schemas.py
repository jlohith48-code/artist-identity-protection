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
