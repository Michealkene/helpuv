# backend/app/routers/users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from typing import List

router = APIRouter()

@router.get("/me")
async def get_current_user(db: Session = Depends(get_db)):
    """Get current user profile"""
    return {
        "id": 1,
        "email": "user@example.com",
        "name": "Test User"
    }

@router.get("/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    return {
        "id": user_id,
        "email": f"user{user_id}@example.com",
        "name": f"User {user_id}"
    }

@router.put("/me")
async def update_profile(db: Session = Depends(get_db)):
    """Update user profile"""
    return {"message": "Profile updated"}