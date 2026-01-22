from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PurchaseCreate(BaseModel):
    dataset_id: int

class PurchaseResponse(BaseModel):
    id: str
    dataset: Optional[dict] = None
    amount: float
    status: str
    payment_url: Optional[str] = None
    created_at: datetime
    paid_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PurchaseListResponse(BaseModel):
    id: str
    dataset: dict
    amount: float
    purchased_at: datetime
    
    class Config:
        from_attributes = True

class RefundRequest(BaseModel):
    reason: str

class RefundResponse(BaseModel):
    id: str
    status: str
    refund_amount: float
    refunded_at: datetime