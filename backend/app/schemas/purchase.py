"""
Purchase schemas - Request/response models for purchase endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================
# Request Schemas
# ============================================================

class PurchaseCreate(BaseModel):
    """Schema for creating a purchase"""
    dataset_id: int


class RefundRequest(BaseModel):
    """Schema for refund request (admin)"""
    reason: str = Field(..., min_length=1, max_length=500)


# ============================================================
# Response Schemas
# ============================================================

class DatasetBrief(BaseModel):
    """Brief dataset info for purchase response"""
    id: int
    name: str
    slug: str
    company_count: int
    enrichment_level: str
    
    class Config:
        from_attributes = True


class PurchaseResponse(BaseModel):
    """Schema for purchase response"""
    id: str
    dataset: Optional[DatasetBrief] = None
    amount_cents: int
    status: str
    paid_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PurchaseDetailResponse(PurchaseResponse):
    """Schema for detailed purchase (admin view)"""
    user_id: str
    user_email: Optional[str] = None
    paystack_reference: str
    refund_amount_cents: Optional[int] = None
    refund_reason: Optional[str] = None
    refunded_at: Optional[datetime] = None


class PurchaseCreateResponse(BaseModel):
    """Schema for purchase creation response"""
    purchase_id: str
    payment_url: str
    amount_cents: int
    message: str = "Redirect to payment page"


class PurchaseAlreadyOwned(BaseModel):
    """Schema when user already owns the dataset"""
    message: str = "You already own this dataset"
    purchase_id: str
    redirect_url: str = "/downloads"


# ============================================================
# Download Schemas
# ============================================================

class DownloadResponse(BaseModel):
    """Schema for download response"""
    download_url: str
    expires_in: int = 3600  # seconds
    filename: str


class DownloadLogResponse(BaseModel):
    """Schema for download log (admin view)"""
    id: int
    purchase_id: str
    user_id: str
    ip_address: str
    user_agent: Optional[str] = None
    country_code: Optional[str] = None
    downloaded_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================
# Paginated Response
# ============================================================

class PaginatedPurchaseResponse(BaseModel):
    """Schema for paginated purchase list"""
    items: List[PurchaseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedPurchaseDetailResponse(BaseModel):
    """Schema for paginated purchase detail list (admin)"""
    items: List[PurchaseDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
