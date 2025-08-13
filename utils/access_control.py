# utils/access_control.py
from datetime import datetime, timedelta
from jose import jwt
from settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
