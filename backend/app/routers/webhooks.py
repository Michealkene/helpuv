from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import hmac
import hashlib
from datetime import datetime
from app.core.database import get_db
from app.core.config import settings
from app.models.purchase import Purchase, PurchaseStatus

router = APIRouter()

@router.post("/paystack")
async def paystack_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Paystack webhook events"""
    # Get signature
    signature = request.headers.get("x-paystack-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    # Verify signature
    body = await request.body()
    expected_signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
        body,
        hashlib.sha512
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Parse event
    event = await request.json()
    
    if event['event'] == 'charge.success':
        # Update purchase status
        reference = event['data']['reference']
        purchase = db.query(Purchase).filter(
            Purchase.paystack_reference == reference
        ).first()
        
        if purchase:
            purchase.status = PurchaseStatus.PAID
            purchase.paid_at = datetime.utcnow()
            db.commit()
            
            # TODO: Send receipt email
    
    return {"status": "success"}