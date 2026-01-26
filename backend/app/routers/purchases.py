from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import List
import uuid
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.models.purchase import Purchase, PurchaseStatus
from app.models.cart import CartItem
from paystackapi.transaction import Transaction
from app.core.config import settings
from app.services.currency_service import CurrencyService

router = APIRouter()

class CreatePurchaseRequest(BaseModel):
    dataset_id: int | None = None  # For direct purchase
    quantity: int | None = None  # For direct purchase
    from_cart: bool = False  # Checkout entire cart

class PurchaseResponse(BaseModel):
    id: str
    dataset: dict | None
    items: List[dict] | None
    amount_usd: float
    amount_naira: float
    exchange_rate: float
    status: str
    payment_url: str | None
    created_at: datetime

@router.post("/", response_model=PurchaseResponse)
async def create_purchase(
    data: CreatePurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new purchase from cart or direct"""
    
    exchange_rate = CurrencyService.get_usd_to_naira_rate()
    items_to_purchase = []
    total_usd = 0
    
    if data.from_cart:
        # Checkout from cart
        cart_items = db.query(CartItem).filter(
            CartItem.user_id == current_user.id
        ).all()
        
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        for item in cart_items:
            price_per_company = 0.05 if item.dataset.enrichment_level == 'phone_only' else 0.10
            subtotal = price_per_company * item.quantity
            total_usd += subtotal
            
            items_to_purchase.append({
                "dataset_id": item.dataset_id,
                "quantity": item.quantity,
                "price_per_company": price_per_company,
                "subtotal": subtotal
            })
    else:
        # Direct purchase
        if not data.dataset_id or not data.quantity:
            raise HTTPException(status_code=400, detail="dataset_id and quantity required for direct purchase")
        
        dataset = db.query(Dataset).filter(
            Dataset.id == data.dataset_id,
            Dataset.is_published == True
        ).first()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        if data.quantity <= 0 or data.quantity > dataset.company_count:
            raise HTTPException(
                status_code=400,
                detail=f"Quantity must be between 1 and {dataset.company_count}"
            )
        
        price_per_company = 0.05 if dataset.enrichment_level == 'phone_only' else 0.10
        subtotal = price_per_company * data.quantity
        total_usd = subtotal
        
        items_to_purchase.append({
            "dataset_id": dataset.id,
            "quantity": data.quantity,
            "price_per_company": price_per_company,
            "subtotal": subtotal
        })
    
    total_naira = total_usd * exchange_rate
    amount_cents_naira = int(total_naira * 100)  # Paystack uses kobo
    
    # For now, create single purchase (in future, support multi-dataset purchases)
    first_item = items_to_purchase[0]
    
    # Create purchase
    purchase = Purchase(
        id=uuid.uuid4(),
        user_id=current_user.id,
        dataset_id=first_item["dataset_id"],
        quantity=first_item["quantity"],
        amount_cents=amount_cents_naira,  # Store in Naira kobo
        amount_usd=round(total_usd, 2),
        amount_naira=round(total_naira, 2),
        exchange_rate=round(exchange_rate, 4),
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
            amount=amount_cents_naira,  # Paystack amount in kobo (Naira cents)
            reference=purchase.paystack_reference,
            callback_url=f"{settings.FRONTEND_URL}/purchase/success?purchase_id={purchase.id}",
            metadata={
                "purchase_id": str(purchase.id),
                "dataset_id": first_item["dataset_id"],
                "quantity": first_item["quantity"],
                "amount_usd": round(total_usd, 2),
                "exchange_rate": round(exchange_rate, 4),
                "user_id": str(current_user.id)
            }
        )
        
        payment_url = response['data']['authorization_url']
    except Exception as e:
        db.delete(purchase)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Payment initiation failed: {str(e)}")
    
    # Clear cart if checkout from cart
    if data.from_cart:
        db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
        db.commit()
    
    dataset_info = db.query(Dataset).filter(Dataset.id == first_item["dataset_id"]).first()
    
    return {
        "id": str(purchase.id),
        "dataset": {
            "id": dataset_info.id,
            "name": dataset_info.name
        } if not data.from_cart else None,
        "items": items_to_purchase if data.from_cart else None,
        "amount_usd": round(total_usd, 2),
        "amount_naira": round(total_naira, 2),
        "exchange_rate": round(exchange_rate, 4),
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
                "total_companies": p.dataset.company_count
            } if p.dataset else None,
            "quantity": p.quantity,
            "amount_usd": float(p.amount_usd) if p.amount_usd else p.amount_cents / 100,
            "amount_naira": float(p.amount_naira) if p.amount_naira else None,
            "purchased_at": p.paid_at
        }
        for p in purchases
    ]
