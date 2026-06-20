from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
# pyrefly: ignore [missing-import]
from passlib.context import CryptContext
# pyrefly: ignore [missing-import]
from motor.motor_asyncio import AsyncIOMotorClient

from config import JWT_SECRET, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Pydantic Models ──────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# ── Helpers ───────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

# ── Routes ────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister):
    db = get_db()
    
    # Check if user exists
    existing_user = await db.users.find_one({"$or": [{"email": user.email}, {"username": user.username}]})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    new_user = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hash_password(user.password),
        "created_at": datetime.now(timezone.utc),
        "test_history": []
    }
    
    await db.users.insert_one(new_user)
    return {"message": "User registered successfully"}

@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    db = get_db()
    
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": db_user["email"], "username": db_user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/profile")
async def get_profile(email: str):
    db = get_db()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Simple stats from test history (this would be expanded based on actual test linking)
    return {
        "username": user["username"],
        "iq_score": user.get("last_iq", 0),
        "coding_rank": user.get("coding_rank", "N/A"),
        "tests_taken": len(user.get("test_history", [])),
        "last_activity": user.get("last_activity", "Never")
    }
