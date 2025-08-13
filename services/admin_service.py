# services/admin_service.py
from model import User
from sqlalchemy.orm import Session
from database import get_db

async def get_user_by_id(user_id: int, db: Session = next(get_db())):
    return db.query(User).filter(User.id == user_id).first()
