from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

# Category schemas
class CategoryBase(BaseModel):
    name: str
    slug: str
    icon: Optional[str] = None
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    id: int
    display_order: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CategorySimple(BaseModel):
    id: int
    name: str
    slug: str
    icon: Optional[str] = None

    class Config:
        from_attributes = True

# Dataset Field schemas
class DatasetFieldResponse(BaseModel):
    field_name: str
    field_label: Optional[str] = None
    is_enriched: bool = False
    display_order: int = 0

    class Config:
        from_attributes = True

# Dataset schemas
class DatasetBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    location: Optional[str] = None

class DatasetCreate(DatasetBase):
    category_id: Optional[int] = None
    company_count: int
    enrichment_level: str
    price_cents: int
    csv_file_path: str
    sample_preview_json: Optional[Dict[str, Any]] = None
    is_published: bool = False

class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    location: Optional[str] = None
    price_cents: Optional[int] = None
    is_published: Optional[bool] = None

class DatasetResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    category: Optional[CategorySimple] = None
    location: Optional[str] = None
    company_count: int
    price: float  # Price in dollars (converted from cents)
    enrichment_level: str
    is_published: bool
    total_purchases: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class DatasetDetail(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    category: Optional[CategorySimple] = None
    location: Optional[str] = None
    company_count: int
    price: float
    enrichment_level: str
    sample_preview: Optional[Dict[str, Any]] = None
    fields: List[DatasetFieldResponse] = []
    total_purchases: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DatasetListResponse(BaseModel):
    datasets: List[DatasetResponse]
    total: int
    page: int = 1
    page_size: int = 20