from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.cart import CartItem
from app.models.dataset import Dataset
from app.helpers import calculate_dataset_price
from app.services.currency_service import CurrencyService

router = APIRouter()

class AddToCartRequest(BaseModel):
    dataset_id: int
    quantity: int  # Number of companies

class UpdateCartItemRequest(BaseModel):
    quantity: int

class CartItemResponse(BaseModel):
    id: str
    dataset: dict
    quantity: int
    price_per_company_usd: float
    subtotal_usd: float
    subtotal_naira: float

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total_usd: float
    total_naira: float
    exchange_rate: float

@router.post("/")
async def add_to_cart(
    data: AddToCartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add item to cart"""
    
    # Validate dataset exists
    dataset = db.query(Dataset).filter(
        Dataset.id == data.dataset_id,
        Dataset.is_published == True
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Validate quantity
    if data.quantity <= 0 or data.quantity > dataset.company_count:
        raise HTTPException(
            status_code=400,
            detail=f"Quantity must be between 1 and {dataset.company_count}"
        )
    
    # Check if item already in cart
    existing = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.dataset_id == data.dataset_id
    ).first()
    
    if existing:
        # Update quantity
        existing.quantity = data.quantity
        db.commit()
        return {"message": "Cart updated", "item_id": str(existing.id)}
    
    # Add new item
    cart_item = CartItem(
        user_id=current_user.id,
        dataset_id=data.dataset_id,
        quantity=data.quantity
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    
    return {"message": "Added to cart", "item_id": str(cart_item.id)}

@router.get("/", response_model=CartResponse)
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's cart"""
    
    cart_items = db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).all()
    
    exchange_rate = CurrencyService.get_usd_to_naira_rate()
    
    items = []
    total_usd = 0
    
    for item in cart_items:
        # Calculate price per company based on enrichment level
        price_per_company_cents = 5 if item.dataset.enrichment_level == 'phone_only' else 10
        price_per_company_usd = price_per_company_cents / 100
        
        subtotal_usd = price_per_company_usd * item.quantity
        subtotal_naira = subtotal_usd * exchange_rate
        
        total_usd += subtotal_usd
        
        items.append({
            "id": str(item.id),
            "dataset": {
                "id": item.dataset.id,
                "name": item.dataset.name,
                "slug": item.dataset.slug,
                "enrichment_level": item.dataset.enrichment_level,
                "total_companies": item.dataset.company_count
            },
            "quantity": item.quantity,
            "price_per_company_usd": price_per_company_usd,
            "subtotal_usd": round(subtotal_usd, 2),
            "subtotal_naira": round(subtotal_naira, 2)
        })
    
    return {
        "items": items,
        "total_usd": round(total_usd, 2),
        "total_naira": round(total_usd * exchange_rate, 2),
        "exchange_rate": exchange_rate
    }

@router.put("/{item_id}")
async def update_cart_item(
    item_id: str,
    data: UpdateCartItemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update cart item quantity"""
    
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    # Validate quantity
    if data.quantity <= 0 or data.quantity > cart_item.dataset.company_count:
        raise HTTPException(
            status_code=400,
            detail=f"Quantity must be between 1 and {cart_item.dataset.company_count}"
        )
    
    cart_item.quantity = data.quantity
    db.commit()
    
    return {"message": "Cart item updated"}

@router.delete("/{item_id}")
async def remove_from_cart(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove item from cart"""
    
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    db.delete(cart_item)
    db.commit()
    
    return {"message": "Item removed from cart"}

@router.delete("/")
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all items from cart"""
    
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    
    return {"message": "Cart cleared"}
