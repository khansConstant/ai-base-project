# app/core/security.py
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()  # load .env file

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET is not set in .env")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

ALGORITHM = os.getenv("ALGORITHM", "HS256")  # default to HS256 if missing


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire_delta = timedelta(minutes=(expires_minutes if expires_minutes is not None else ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": subject, "exp": datetime.utcnow() + expire_delta}
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise e
