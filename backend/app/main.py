from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Artist Protection System",
    description="Protecting lyricists and artists from identity theft and fraud",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "Artist Protection System is running!",
        "status": "active"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}