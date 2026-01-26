"""
Dataset schemas - Request/response models for dataset endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ============================================================
# Category Schemas
# ============================================================

class CategoryResponse(BaseModel):
    """Schema for category response"""
    id: int
    name: str
    slug: str
    icon: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================================
# Dataset Field Schemas
# ============================================================

class DatasetFieldResponse(BaseModel):
    """Schema for dataset field (what's included)"""
    id: int
    field_name: str
    field_label: Optional[str] = None
    is_enriched: bool = False
    display_order: int = 0
    
    class Config:
        from_attributes = True


# ============================================================
# Dataset Schemas
# ============================================================

class DatasetBase(BaseModel):
    """Base dataset schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    enrichment_level: str = Field(default="phone_only", pattern="^(phone_only|email_and_phone)$")
    price_cents: int = Field(..., gt=0)


class DatasetCreate(DatasetBase):
    """Schema for creating a dataset (admin)"""
    category_id: Optional[int] = None
    company_count: int = Field(default=0, ge=0)
    csv_file_path: Optional[str] = None
    sample_preview_json: Optional[str] = None


class DatasetUpdate(BaseModel):
    """Schema for updating a dataset (admin)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    location: Optional[str] = None
    category_id: Optional[int] = None
    company_count: Optional[int] = Field(None, ge=0)
    enrichment_level: Optional[str] = Field(None, pattern="^(phone_only|email_and_phone)$")
    price_cents: Optional[int] = Field(None, gt=0)
    is_published: Optional[bool] = None
    csv_file_path: Optional[str] = None


class DatasetListResponse(BaseModel):
    """Schema for dataset list (browse page)"""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    location: Optional[str] = None
    company_count: int
    enrichment_level: str
    price_cents: int
    category: Optional[CategoryResponse] = None
    total_purchases: int = 0
    
    class Config:
        from_attributes = True


class DatasetDetailResponse(BaseModel):
    """Schema for dataset detail page"""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    location: Optional[str] = None
    company_count: int
    enrichment_level: str
    price_cents: int
    category: Optional[CategoryResponse] = None
    fields: List[DatasetFieldResponse] = []
    sample_preview_json: Optional[List[dict]] = None
    total_purchases: int = 0
    last_updated_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DatasetAdminResponse(DatasetDetailResponse):
    """Schema for dataset admin view (includes additional fields)"""
    is_published: bool
    csv_file_path: Optional[str] = None
    total_revenue_cents: int = 0
    updated_at: datetime


# ============================================================
# Filter Schemas
# ============================================================

class DatasetFilters(BaseModel):
    """Schema for dataset browse filters"""
    category: Optional[str] = None
    location: Optional[str] = None
    min_price: Optional[int] = Field(None, ge=0)
    max_price: Optional[int] = Field(None, ge=0)
    enrichment_level: Optional[str] = Field(None, pattern="^(phone_only|email_and_phone)$")


# ============================================================
# Paginated Response
# ============================================================

class PaginatedDatasetResponse(BaseModel):
    """Schema for paginated dataset list"""
    items: List[DatasetListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
