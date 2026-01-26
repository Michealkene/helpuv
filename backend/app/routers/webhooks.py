"""
Webhooks Router - Handle Paystack payment webhooks
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.purchase import Purchase
from app.models.user import User
from app.services.payment_service import PaymentService
from app.services.email_service import EmailService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/paystack")
async def paystack_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Paystack webhook events.
    
    Events handled:
    - charge.success: Payment completed successfully
    
    Security:
    - Verifies webhook signature
    - Uses idempotent reference to prevent double processing
    """
    # 1. Verify signature
    signature = request.headers.get("x-paystack-signature")
    if not signature:
        logger.warning("Webhook received without signature")
        raise HTTPException(status_code=400, detail="Missing signature")
    
    body = await request.body()
    
    if not PaymentService.verify_webhook_signature(body, signature):
        logger.warning(f"Invalid webhook signature from {request.client.host}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # 2. Parse event
    try:
        event = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook body: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    event_type = event.get("event")
    data = event.get("data", {})
    
    logger.info(f"Received Paystack webhook: {event_type}")
    
    # 3. Handle event
    if event_type == "charge.success":
        await handle_charge_success(data, db)
    elif event_type == "charge.failed":
        await handle_charge_failed(data, db)
    elif event_type == "refund.processed":
        await handle_refund_processed(data, db)
    else:
        # Log but don't fail for unknown events
        logger.info(f"Unhandled webhook event: {event_type}")
    
    return {"status": "success"}


async def handle_charge_success(data: dict, db: Session):
    """
    Handle successful payment.
    
    - Updates purchase status to "paid"
    - Records authorization code for future use
    - Sends receipt email
    """
    reference = data.get("reference")
    
    if not reference:
        logger.error("charge.success without reference")
        return
    
    # Find purchase
    purchase = db.query(Purchase).filter(
        Purchase.paystack_reference == reference
    ).first()
    
    if not purchase:
        logger.error(f"Purchase not found for reference: {reference}")
        return
    
    # Check if already processed (idempotency)
    if purchase.status == "paid":
        logger.info(f"Purchase {purchase.id} already paid, skipping")
        return
    
    # Update purchase
    purchase.status = "paid"
    purchase.paid_at = datetime.utcnow()
    
    # Store authorization code (for subscriptions later)
    authorization = data.get("authorization", {})
    if authorization.get("authorization_code"):
        purchase.paystack_authorization_code = authorization["authorization_code"]
    
    db.commit()
    
    logger.info(f"Purchase {purchase.id} marked as paid")
    
    # Send receipt email
    try:
        user = db.query(User).filter(User.id == purchase.user_id).first()
        dataset = purchase.dataset
        
        if user and dataset:
            email_service = EmailService()
            await email_service.send_purchase_receipt(
                email=user.email,
                name=user.name,
                dataset_name=dataset.name,
                amount_cents=purchase.amount_cents,
                purchase_id=str(purchase.id)
            )
    except Exception as e:
        logger.error(f"Failed to send receipt email: {e}")


async def handle_charge_failed(data: dict, db: Session):
    """
    Handle failed payment.
    
    - Updates purchase status to "failed"
    """
    reference = data.get("reference")
    
    if not reference:
        return
    
    purchase = db.query(Purchase).filter(
        Purchase.paystack_reference == reference
    ).first()
    
    if not purchase:
        return
    
    # Don't change if already paid or refunded
    if purchase.status in ["paid", "refunded"]:
        return
    
    purchase.status = "failed"
    db.commit()
    
    logger.info(f"Purchase {purchase.id} marked as failed")


async def handle_refund_processed(data: dict, db: Session):
    """
    Handle refund completion.
    
    - Confirms refund was processed by Paystack
    """
    reference = data.get("transaction", {}).get("reference")
    
    if not reference:
        return
    
    purchase = db.query(Purchase).filter(
        Purchase.paystack_reference == reference
    ).first()
    
    if not purchase:
        return
    
    # Refund should already be marked by admin, just log
    logger.info(f"Refund confirmed by Paystack for purchase {purchase.id}")
