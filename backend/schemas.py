
from pydantic import BaseModel
import datetime
from typing import List, Optional

class VideoBase(BaseModel):
    title: str
    original_text: str
    template: str

class VideoCreate(VideoBase):
    pass

class Video(VideoBase):
    id: int
    user_id: int
    video_url: Optional[str] = None
    status: str
    created_at: datetime.datetime

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    video_quota: int
    videos: List[Video] = []

    class Config:
        orm_mode = True
