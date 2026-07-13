from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
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
