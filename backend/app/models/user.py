"""
User model - Maps to your existing users table
"""

from sqlalchemy import Column, String, Boolean, TIMESTAMP, Integer, Numeric, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class User(Base):
    """
    User model - Maps to your existing users table.
    This is used for the Helpuvio marketplace authentication.
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    name = Column(String(100), nullable=False)
    avatar_url = Column(String(500))
    
    # Location (from your existing schema)
    latitude = Column(Numeric)
    longitude = Column(Numeric)
    city = Column(String(255))
    state = Column(String(255))
    country = Column(String(255))
    postal_code = Column(String(50))
    
    # Status
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    onboarding_completed = Column(Boolean, default=False)
    
    # Password reset
    password_reset_token = Column(String(255))
    password_reset_expires = Column(TIMESTAMP(timezone=True))
    email_verify_token = Column(String(255))
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    last_login_at = Column(TIMESTAMP(timezone=True))
    
    # Relationships
    purchases = relationship("Purchase", back_populates="user", lazy="dynamic")
    refresh_tokens = relationship("RefreshToken", back_populates="user", lazy="dynamic")
    download_logs = relationship("DownloadLog", back_populates="user", lazy="dynamic")
    cart_items = relationship("CartItem", back_populates="user", lazy="dynamic")
    
    def __repr__(self):
        return f"<User {self.email}>"


class RefreshToken(Base):
    """
    Refresh token model for JWT authentication.
    Maps to your existing refresh_tokens table.
    """
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(500), unique=True, nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    revoked_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<RefreshToken {self.id}>"
