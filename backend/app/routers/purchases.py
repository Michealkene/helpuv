from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import uuid
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.models.purchase import Purchase, PurchaseStatus
from paystackapi.transaction import Transaction
from app.core.config import settings

router = APIRouter()

class CreatePurchaseRequest(BaseModel):
    dataset_id: int

class PurchaseResponse(BaseModel):
    id: str
    dataset: dict
    amount: float
    status: str
    payment_url: str | None
    created_at: datetime

@router.post("/", response_model=PurchaseResponse)
async def create_purchase(
    data: CreatePurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new purchase"""
    # Check dataset exists
    dataset = db.query(Dataset).filter(
        Dataset.id == data.dataset_id,
        Dataset.is_published == True
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Check if already purchased
    existing = db.query(Purchase).filter(
        Purchase.user_id == current_user.id,
        Purchase.dataset_id == dataset.id,
        Purchase.status == PurchaseStatus.PAID
    ).first()
    
    if existing:
        return {
            "id": str(existing.id),
            "dataset": {"id": dataset.id, "name": dataset.name},
            "amount": existing.amount_cents / 100,
            "status": existing.status,
            "payment_url": None,
            "created_at": existing.created_at
        }
    
    # Create purchase
    purchase = Purchase(
        id=uuid.uuid4(),
        user_id=current_user.id,
        dataset_id=dataset.id,
        amount_cents=dataset.price_cents,
        paystack_reference=f"PUR-{uuid.uuid4().hex[:12].upper()}",
        status=PurchaseStatus.PENDING
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    
    # Create Paystack payment link
    try:
        response = Transaction.initialize(
            email=current_user.email,
            amount=dataset.price_cents,  # Paystack uses kobo (cents)
            reference=purchase.paystack_reference,
            callback_url=f"{settings.FRONTEND_URL}/purchase/success?purchase_id={purchase.id}",
            metadata={
                "purchase_id": str(purchase.id),
                "dataset_name": dataset.name,
                "user_id": str(current_user.id)
            }
        )
        
        payment_url = response['data']['authorization_url']
    except Exception as e:
        db.delete(purchase)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Payment initiation failed: {str(e)}")
    
    return {
        "id": str(purchase.id),
        "dataset": {"id": dataset.id, "name": dataset.name},
        "amount": purchase.amount_cents / 100,
        "status": purchase.status,
        "payment_url": payment_url,
        "created_at": purchase.created_at
    }

@router.get("/my-purchases")
async def list_my_purchases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List current user's purchases"""
    purchases = db.query(Purchase).filter(
        Purchase.user_id == current_user.id,
        Purchase.status == PurchaseStatus.PAID
    ).order_by(Purchase.paid_at.desc()).all()
    
    return [
        {
            "id": str(p.id),
            "dataset": {
                "id": p.dataset.id,
                "name": p.dataset.name,
                "slug": p.dataset.slug,
                "company_count": p.dataset.company_count
            } if p.dataset else None,
            "amount": p.amount_cents / 100,
            "purchased_at": p.paid_at
        }
        for p in purchases
    ]