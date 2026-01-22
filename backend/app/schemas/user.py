from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    id: str
    avatar_url: Optional[str] = None
    email_verified: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    credential: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str