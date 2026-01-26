from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class AdminResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class AdminTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    admin: AdminResponse

class DashboardStatsResponse(BaseModel):
    total_users: int
    total_datasets: int
    total_purchases: int
    total_revenue: float
    revenue_this_month: float
    purchases_this_month: int
    signups_this_month: int

class DatasetStatsResponse(BaseModel):
    id: int
    name: str
    total_purchases: int
    total_revenue: float