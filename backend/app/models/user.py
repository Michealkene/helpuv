from sqlalchemy import Column, String, Boolean, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100))
    avatar_url = Column(String(500))
    
    # Google OAuth
    google_id = Column(String(100), unique=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('NOW()'), onupdate=text('NOW()'))
    last_login_at = Column(TIMESTAMP(timezone=True))
    
    # Relationships
    purchases = relationship("Purchase", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    download_logs = relationship("DownloadLog", back_populates="user")