from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.models.user import User
from app.models.purchase import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests
from app.core.config import settings

router = APIRouter()

# Schemas
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    credential: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

# Signup
@router.post("/signup", response_model=TokenResponse)
async def signup(data: SignupRequest, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password
    if len(data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Create user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
        email_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create tokens
    access_token = create_access_token({"sub": str(user.id), "email": user.email, "role": "user"})
    refresh_token_str = create_refresh_token({"sub": str(user.id)})
    
    # Save refresh token
    refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "avatar_url": user.avatar_url
        }
    }

# Login
@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    # Find user
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token({"sub": str(user.id), "email": user.email, "role": "user"})
    refresh_token_str = create_refresh_token({"sub": str(user.id)})
    
    # Save refresh token
    refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(refresh_token)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "avatar_url": user.avatar_url
        }
    }

# Google OAuth
@router.post("/google", response_model=TokenResponse)
async def google_auth(data: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            data.credential,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        
        email = idinfo.get("email")
        name = idinfo.get("name")
        picture = idinfo.get("picture")
        google_id = idinfo.get("sub")
        
        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            user = User(
                email=email,
                name=name,
                avatar_url=picture,
                google_id=google_id,
                password_hash="",  # OAuth users have no password
                email_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update Google ID if not set
            if not user.google_id:
                user.google_id = google_id
            user.last_login_at = datetime.utcnow()
            db.commit()
        
        # Create tokens
        access_token = create_access_token({"sub": str(user.id), "email": user.email, "role": "user"})
        refresh_token_str = create_refresh_token({"sub": str(user.id)})
        
        # Save refresh token
        refresh_token = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(refresh_token)
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "avatar_url": user.avatar_url
            }
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )