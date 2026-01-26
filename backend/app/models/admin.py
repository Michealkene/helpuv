"""
Admin models - Separate admin users and audit logging
"""

from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class AdminUser(Base):
    """
    Admin user model - Separate from regular users.
    
    Roles:
    - admin: Can manage datasets and view purchases
    - superadmin: Can manage other admins and issue refunds
    """
    __tablename__ = "admin_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    name = Column(String(100), nullable=False)
    
    # Role: admin, superadmin
    role = Column(String(50), default="admin")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    last_login_at = Column(TIMESTAMP(timezone=True))
    
    # Relationships
    audit_logs = relationship("AdminAuditLog", back_populates="admin")
    
    @property
    def is_superadmin(self) -> bool:
        """Check if admin has superadmin role"""
        return self.role == "superadmin"
    
    def __repr__(self):
        return f"<AdminUser {self.email}>"


class AdminAuditLog(Base):
    """
    Audit log for admin actions - For compliance and debugging.
    """
    __tablename__ = "admin_audit_logs"
    
    id = Column(Integer, primary_key=True)
    
    # Who did what
    admin_id = Column(UUID(as_uuid=True), ForeignKey("admin_users.id"))
    action = Column(String(100), nullable=False)  # "create_dataset", "issue_refund"
    
    # What was affected
    resource_type = Column(String(50))  # "dataset", "purchase", "user"
    resource_id = Column(String(100))
    
    # Additional context
    details = Column(JSONB)
    
    # Request metadata
    ip_address = Column(INET)
    
    # When
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    
    # Relationships
    admin = relationship("AdminUser", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AdminAuditLog {self.action}>"


class DailyMetric(Base):
    """
    Daily aggregated metrics for analytics dashboard.
    """
    __tablename__ = "daily_metrics"
    
    id = Column(Integer, primary_key=True)
    date = Column(TIMESTAMP(timezone=True), unique=True, nullable=False, index=True)
    
    # Counts
    signups = Column(Integer, default=0)
    purchases = Column(Integer, default=0)
    downloads = Column(Integer, default=0)
    
    # Revenue
    revenue_cents = Column(Integer, default=0)
    
    # Timestamp
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    
    def __repr__(self):
        return f"<DailyMetric {self.date}>"
