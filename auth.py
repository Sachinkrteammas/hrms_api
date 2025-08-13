from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from model import User, UserMeta
from schemas import UserSignUpDTO, UserLogInDTO
from database import get_db
from utils.access_control import create_access_token
import hashlib
import secrets

router = APIRouter()

def encode_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_random_string(length: int = 30) -> str:
    return secrets.token_urlsafe(length)[:length]

@router.post("/signup")
def signup(dto: UserSignUpDTO, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == dto.email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not allowed to signup")

    if user.meta:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User already exists")

    if dto.pass_code != user.pass_code:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Pass code does not match")

    user.password = encode_password(dto.password)
    user.access_token = generate_random_string()

    user_meta = UserMeta(name=dto.name, user=user)
    db.add(user_meta)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "access_token": user.access_token,
        "name": user.meta.name
    }


@router.post("/login")
def login(dto: UserLogInDTO, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == dto.email).first()

    if not user or user.password != encode_password(dto.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid email or password"
        )

    # Create JWT token
    access_token = create_access_token(data={"sub": str(user.id)})

    # Update user's access token in database
    user.access_token = access_token
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "access_token": access_token,
        "token_type": "bearer"
    }
