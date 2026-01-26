"""
SQLAlchemy database models
"""
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class User(Base):
    """User accounts table"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100))
    password_hash = Column(String(255))  # Optional for OAuth users
    
    # OAuth fields
    google_id = Column(String(255), unique=True, index=True)
    profile_picture = Column(String(500))
    oauth_provider = Column(String(50))  # 'google', 'email', etc.
    
    # Verification
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    # Relationships
    purchases = relationship("Purchase", back_populates="user")


class Dataset(Base):
    """Datasets table - Products for sale"""
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # Classification
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    location = Column(String(200))
    
    # Metadata
    company_count = Column(Integer, default=0)
    enrichment_level = Column(String(50), default="phone_only", index=True)
    
    # Pricing
    price_cents = Column(Integer, nullable=False, index=True)
    
    # File storage
    csv_file_path = Column(String(500))
    sample_preview_json = Column(JSONB)
    
    # Publishing
    is_published = Column(Boolean, default=False, index=True)
    
    # Stats
    total_purchases = Column(Integer, default=0)
    total_revenue_cents = Column(BigInteger, default=0)
    
    # Timestamps
    last_updated_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    purchases = relationship("Purchase", back_populates="dataset")


class Purchase(Base):
    """Purchases table - Revenue tracking"""
    __tablename__ = "purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="SET NULL"))
    
    # Payment details
    amount_cents = Column(Integer, nullable=False)
    paystack_reference = Column(String(200), unique=True, nullable=False, index=True)
    paystack_authorization_code = Column(String(200))
    
    # Status
    status = Column(String(50), default="pending", index=True)
    
    # Refund tracking
    refund_amount_cents = Column(Integer)
    refund_reason = Column(Text)
    refunded_by = Column(UUID(as_uuid=True))
    refunded_at = Column(DateTime)
    
    # Timestamps
    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="purchases")
    dataset = relationship("Dataset", back_populates="purchases")


class DownloadLog(Base):
    """Download logs - Audit trail"""
    __tablename__ = "download_logs"

    id = Column(Integer, primary_key=True)
    purchase_id = Column(UUID(as_uuid=True), ForeignKey("purchases.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="SET NULL"))
    
    # Request metadata
    ip_address = Column(INET, nullable=False, index=True)
    user_agent = Column(Text)
    country_code = Column(String(5))
    
    downloaded_at = Column(DateTime, default=datetime.utcnow, index=True)


class AdminUser(Base):
    """Admin users table"""
    __tablename__ = "admin_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(50), default="admin")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime)


class Category(Base):
    """Categories table (if not exists in your schema)"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)