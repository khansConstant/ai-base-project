# app/api/v1/endpoints/auth.py

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

load_dotenv()  # load .env file

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET is not set in .env")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

ALGORITHM = os.getenv("ALGORITHM", "HS256")  # default to HS256 if missing




from app.core.supabase import supabase  # your Supabase client

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# -------------------------------
# Security setup with Argon2
# -------------------------------
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# JWT config


# -------------------------------
# Pydantic Schemas
# -------------------------------
class RegisterPayload(BaseModel):
    username: str
    email: EmailStr
    password: str
    company_name: str
    contact_number: str

class LoginPayload(BaseModel):
    email: EmailStr
    password: str

# -------------------------------
# Helper functions
# -------------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# -------------------------------
# Supabase helpers
# -------------------------------
def get_user_by_email(email: str):
    res = supabase.table("users").select("*").eq("email", email).execute()
    if res.data and len(res.data) > 0:
        return res.data[0]
    return None

def get_user_by_username(username: str):
    res = supabase.table("users").select("*").eq("username", username).execute()
    if res.data and len(res.data) > 0:
        return res.data[0]
    return None

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user_id

# -------------------------------
# Endpoints
# -------------------------------
@router.post("/register")
def register_user(payload: RegisterPayload):
    # check existing users
    if get_user_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if get_user_by_username(payload.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = hash_password(payload.password)
    created_at = datetime.utcnow().isoformat()

    user_data = {
        "username": payload.username,
        "email": payload.email,
        "password": hashed_password,
        "company_name": payload.company_name,
        "contact_number": payload.contact_number,
        "created_at": created_at
    }

    res = supabase.table("users").insert(user_data).execute()

    # Validate insert succeeded
    if not getattr(res, "data", None) or len(res.data) == 0:
        raise HTTPException(status_code=500, detail="Error creating user")

    user_id = res.data[0].get("id")
    if not user_id:
        raise HTTPException(status_code=500, detail="Created user id not returned")

    return {"access_token": create_access_token({"sub": user_id}), "token_type": "bearer"}



@router.post("/login")
def login_user(payload: LoginPayload):
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token({"sub": user["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
def me(user_id: str = Depends(get_current_user_id)):
    res = supabase.table("users")\
        .select("id, username, email, company_name, contact_number, created_at")\
        .eq("id", user_id).execute()
    
    if not res.data or len(res.data) == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return res.data[0]
