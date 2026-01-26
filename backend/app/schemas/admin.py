"""
Admin schemas - Request/response models for admin endpoints
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ============================================================
# Admin Auth Schemas
# ============================================================

class AdminLogin(BaseModel):
    """Schema for admin login"""
    email: EmailStr
    password: str


class AdminCreate(BaseModel):
    """Schema for creating an admin (superadmin only)"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="admin", pattern="^(admin|superadmin)$")


class AdminResponse(BaseModel):
    """Schema for admin response"""
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AdminAuthResponse(BaseModel):
    """Schema for admin auth response"""
    access_token: str
    token_type: str = "bearer"
    admin: AdminResponse


# ============================================================
# Dashboard Schemas
# ============================================================

class DashboardStats(BaseModel):
    """Schema for admin dashboard stats"""
    total_revenue_cents: int
    total_purchases: int
    total_users: int
    total_datasets: int
    
    # This month
    revenue_this_month: int
    purchases_this_month: int
    signups_this_month: int
    
    # Change percentages
    revenue_change: Optional[float] = None
    purchases_change: Optional[float] = None
    signups_change: Optional[float] = None


class RevenueDataPoint(BaseModel):
    """Schema for revenue chart data point"""
    date: str
    revenue_cents: int
    purchases: int


class DashboardResponse(BaseModel):
    """Schema for dashboard response"""
    stats: DashboardStats
    revenue_chart: List[RevenueDataPoint]
    top_datasets: List[dict]
    recent_purchases: List[dict]


# ============================================================
# Audit Log Schemas
# ============================================================

class AuditLogResponse(BaseModel):
    """Schema for audit log response"""
    id: int
    admin_id: str
    admin_email: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaginatedAuditLogResponse(BaseModel):
    """Schema for paginated audit logs"""
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================
# User Management Schemas (Admin)
# ============================================================

class UserAdminResponse(BaseModel):
    """Schema for user in admin view"""
    id: str
    email: str
    name: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    total_purchases: int = 0
    total_spent_cents: int = 0
    
    class Config:
        from_attributes = True


class PaginatedUserResponse(BaseModel):
    """Schema for paginated user list"""
    items: List[UserAdminResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserStatusUpdate(BaseModel):
    """Schema for updating user status"""
    is_active: bool
