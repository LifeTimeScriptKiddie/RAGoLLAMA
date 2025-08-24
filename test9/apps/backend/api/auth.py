from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict, Any
import hashlib
import os
from datetime import timedelta

from apps.backend.core.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["authentication"])

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False

# Simple in-memory user store (use database in production)
# Default admin user
USERS_DB = {
    "admin": {
        "username": "admin",
        "password_hash": hashlib.sha256("admin".encode()).hexdigest(),  # Change in production!
        "is_admin": True
    }
}

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hashlib.sha256(plain_password.encode()).hexdigest() == password_hash

def get_user(username: str) -> Dict[str, Any]:
    """Get user from database."""
    return USERS_DB.get(username)

def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """Authenticate user credentials."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint to get access token."""
    
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "is_admin": user["is_admin"]},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
async def register(user_data: UserCreate):
    """Register new user (admin only in production)."""
    
    # In production, this should require admin authentication
    # For demo, allow open registration
    
    if user_data.username in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Hash password
    password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
    
    # Add user to database
    USERS_DB[user_data.username] = {
        "username": user_data.username,
        "password_hash": password_hash,
        "is_admin": user_data.is_admin
    }
    
    return {"message": "User registered successfully", "username": user_data.username}

@router.get("/users")
async def list_users():
    """List all users (for demo purposes)."""
    return {
        "users": [
            {"username": user["username"], "is_admin": user["is_admin"]}
            for user in USERS_DB.values()
        ]
    }

@router.get("/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information."""
    from apps.backend.core.auth import get_current_user
    return {
        "username": current_user["user_id"],
        "is_admin": current_user.get("is_admin", False)
    }