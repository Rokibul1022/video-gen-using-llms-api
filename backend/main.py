
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import time
import asyncio


from . import crud, models, schemas
from .database import SessionLocal, engine
from pydantic import BaseModel
from .ai_pipeline import process_video_pipeline
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allows the React app to communicate
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Note: The path to the static directory should be relative to where the command is run.
# Running `uvicorn main:app` from the `backend` directory means the path is `static/videos`.
app.mount("/videos", StaticFiles(directory="static/videos"), name="videos")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/{user_id}/videos", response_model=list[schemas.Video])
def read_user_videos(user_id: int, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    videos = crud.get_videos_by_user(db, user_id=user_id, skip=skip, limit=limit)
    return videos


# Request schema for video generation
class GenerateVideoRequest(BaseModel):
    text: str
    template: str
    voice_type: str
    user_id: str

@app.post("/generate-video")
async def generate_video(req: GenerateVideoRequest):
    """Endpoint to generate educational video from text input."""
    out_dir = os.path.join("static", "videos")
    elevenlabs_api_key = "sk_ba0a244e846b46b2cfd76474afca7e11c5b54b5048686167"
    result = process_video_pipeline(
        text=req.text,
        template=req.template,
        voice_type=req.voice_type,
        user_id=req.user_id,
        out_dir=out_dir,
        duration=60,
        elevenlabs_api_key=elevenlabs_api_key
    )
    return result

@app.get("/video-status/{video_id}")
async def get_video_status(video_id: str):
    # In a real app, you would fetch this from the database
    # For this mock, we'll just return a completed status
    return {"video_id": video_id, "status": "completed", "video_url": "/videos/sample.mp4"}

