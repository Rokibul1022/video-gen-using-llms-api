
from sqlalchemy.orm import Session
from . import models, schemas

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_videos_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.Video).filter(models.Video.user_id == user_id).offset(skip).limit(limit).all()

def create_user_video(db: Session, video: schemas.VideoCreate, user_id: int):
    db_video = models.Video(**video.dict(), user_id=user_id)
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video
