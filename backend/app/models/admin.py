from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(50), default="admin")
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('NOW()'))
    last_login_at = Column(TIMESTAMP(timezone=True))
    
    # Relationships
    audit_logs = relationship("AdminAuditLog", back_populates="admin")

class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("admin_users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    details = Column(JSONB)
    ip_address = Column(INET)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('NOW()'))
    
    # Relationships
    admin = relationship("AdminUser", back_populates="audit_logs")