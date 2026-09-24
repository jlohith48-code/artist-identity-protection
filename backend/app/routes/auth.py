from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

from app.database import get_db
from app.models.artist import Artist
from app.utils.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class ArtistRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    iprs_id: Optional[str] = None
    state: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    artist_id: str
    full_name: str
    email: str
    role: str

@router.post("/register", response_model=TokenResponse)
def register(artist_data: ArtistRegister, db: Session = Depends(get_db)):
    existing = db.query(Artist).filter(Artist.email == artist_data.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="An artist account with this email already exists."
        )

    if len(artist_data.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long."
        )

    new_artist = Artist(
        full_name=artist_data.full_name,
        email=artist_data.email.lower(),
        hashed_password=hash_password(artist_data.password),
        phone=artist_data.phone,
        iprs_id=artist_data.iprs_id,
        state=artist_data.state,
        role="artist"
    )
    db.add(new_artist)
    db.commit()
    db.refresh(new_artist)

    token = create_access_token({
        "sub": str(new_artist.id),
        "email": new_artist.email,
        "name": new_artist.full_name,
        "role": new_artist.role
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "artist_id": str(new_artist.id),
        "full_name": new_artist.full_name,
        "email": new_artist.email,
        "role": new_artist.role
    }

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.email == login_data.email.lower()).first()
    if not artist or not artist.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not verify_password(login_data.password, artist.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token({
        "sub": str(artist.id),
        "email": artist.email,
        "name": artist.full_name,
        "role": artist.role or "artist"
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "artist_id": str(artist.id),
        "full_name": artist.full_name,
        "email": artist.email,
        "role": artist.role or "artist"
    }

@router.post("/token", response_model=TokenResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.email == form_data.username.lower()).first()
    if not artist or not artist.hashed_password or not verify_password(form_data.password, artist.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({
        "sub": str(artist.id),
        "email": artist.email,
        "name": artist.full_name,
        "role": artist.role or "artist"
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "artist_id": str(artist.id),
        "full_name": artist.full_name,
        "email": artist.email,
        "role": artist.role or "artist"
    }

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == current_user["sub"]).first()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist profile not found.")
    return {
        "id": str(artist.id),
        "full_name": artist.full_name,
        "email": artist.email,
        "phone": artist.phone,
        "iprs_id": artist.iprs_id,
        "state": artist.state,
        "role": artist.role or "artist",
        "created_at": artist.created_at
    }
