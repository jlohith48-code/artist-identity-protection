import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes import artists, songs, profiles, reports, evidence, auth, conflicts

load_dotenv()

app = FastAPI(
    title="Artist Protection System",
    description="Protecting lyricists and artists from identity theft and streaming fraud",
    version="2.0.0"
)

cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
else:
    origins = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(artists.router)
app.include_router(songs.router)
app.include_router(profiles.router)
app.include_router(reports.router)
app.include_router(evidence.router)
app.include_router(conflicts.router)

@app.get("/")
def home():
    return {
        "message": "Artist Protection System API v2.0 is running!",
        "status": "active"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "2.0.0"}
