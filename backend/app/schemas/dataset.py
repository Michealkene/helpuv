from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CategoryBase(BaseModel):
    name: str
    slug: str
    icon: Optional[str] = None
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int
    display_order: int
    is_active: bool
    
    class Config:
        from_attributes = True

class DatasetFieldBase(BaseModel):
    field_name: str
    field_label: str
    is_enriched: bool = False

class DatasetFieldResponse(DatasetFieldBase):
    id: int
    display_order: int
    
    class Config:
        from_attributes = True

class DatasetBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    location: Optional[str] = None
    category_id: Optional[int] = None
    company_count: int
    enrichment_level: str
    price_cents: int

class DatasetCreate(DatasetBase):
    fields: List[DatasetFieldBase] = []

class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    category_id: Optional[int] = None
    price_cents: Optional[int] = None
    is_published: Optional[bool] = None

class DatasetResponse(DatasetBase):
    id: int
    category: Optional[CategoryResponse] = None
    sample_preview_json: Optional[List] = None
    is_published: bool
    total_purchases: int
    total_revenue_cents: int
    is_purchased: bool = False
    created_at: datetime
    updated_at: datetime
    fields: List[DatasetFieldResponse] = []
    
    class Config:
        from_attributes = True

class DatasetListResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    location: Optional[str] = None
    company_count: int
    price: float
    category: Optional[dict] = None
    total_purchases: int
    is_purchased: bool = False
    
    class Config:
        from_attributes = True