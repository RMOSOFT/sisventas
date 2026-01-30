from app.db.session import SessionLocal
from fastapi import Depends, Cookie, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models import Usuario

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()