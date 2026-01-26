"""
Payment Service - Paystack integration for processing payments
"""

import httpx
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service for handling Paystack payments.
    
    Flow:
    1. Create payment link -> returns authorization_url
    2. User pays on Paystack page
    3. Paystack sends webhook to our /webhooks/paystack endpoint
    4. We verify and mark purchase as paid
    """
    
    BASE_URL = "https://api.paystack.co"
    
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
    
    async def initialize_transaction(
        self,
        email: str,
        amount_cents: int,
        reference: str,
        callback_url: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Initialize a Paystack transaction.
        
        Args:
            email: Customer email
            amount_cents: Amount in smallest currency unit (kobo/cents)
            reference: Unique transaction reference
            callback_url: URL to redirect after payment
            metadata: Additional data to store with transaction
            
        Returns:
            dict with authorization_url, access_code, reference
        """
        if not callback_url:
            callback_url = f"{settings.FRONTEND_URL}/purchase/success"
        
        payload = {
            "email": email,
            "amount": amount_cents,  # Paystack expects kobo/cents
            "reference": reference,
            "callback_url": callback_url,
            "metadata": metadata or {}
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/transaction/initialize",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status"):
                    return {
                        "authorization_url": data["data"]["authorization_url"],
                        "access_code": data["data"]["access_code"],
                        "reference": data["data"]["reference"]
                    }
                else:
                    logger.error(f"Paystack init failed: {data}")
                    raise Exception(f"Payment initialization failed: {data.get('message')}")
                    
            except httpx.HTTPError as e:
                logger.error(f"Paystack HTTP error: {e}")
                raise Exception(f"Payment service unavailable: {str(e)}")
    
    async def verify_transaction(self, reference: str) -> dict:
        """
        Verify a Paystack transaction.
        
        Args:
            reference: Transaction reference to verify
            
        Returns:
            dict with status, amount, paid_at, customer info
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/transaction/verify/{reference}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status"):
                    tx_data = data["data"]
                    return {
                        "status": tx_data["status"],  # "success", "failed", "abandoned"
                        "amount": tx_data["amount"],
                        "paid_at": tx_data.get("paid_at"),
                        "authorization_code": tx_data.get("authorization", {}).get("authorization_code"),
                        "customer": {
                            "email": tx_data.get("customer", {}).get("email")
                        },
                        "metadata": tx_data.get("metadata", {})
                    }
                else:
                    logger.error(f"Paystack verify failed: {data}")
                    raise Exception(f"Payment verification failed: {data.get('message')}")
                    
            except httpx.HTTPError as e:
                logger.error(f"Paystack HTTP error: {e}")
                raise Exception(f"Payment verification unavailable: {str(e)}")
    
    async def refund_transaction(
        self,
        transaction_reference: str,
        amount_cents: Optional[int] = None
    ) -> dict:
        """
        Initiate a refund for a transaction.
        
        Args:
            transaction_reference: Reference of transaction to refund
            amount_cents: Partial refund amount (None for full refund)
            
        Returns:
            dict with refund status and details
        """
        payload = {
            "transaction": transaction_reference
        }
        
        if amount_cents:
            payload["amount"] = amount_cents
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/refund",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status"):
                    return {
                        "status": data["data"]["status"],
                        "refund_amount": data["data"]["amount"],
                        "transaction_reference": data["data"]["transaction"]["reference"]
                    }
                else:
                    logger.error(f"Paystack refund failed: {data}")
                    raise Exception(f"Refund failed: {data.get('message')}")
                    
            except httpx.HTTPError as e:
                logger.error(f"Paystack HTTP error: {e}")
                raise Exception(f"Refund service unavailable: {str(e)}")
    
    @staticmethod
    def verify_webhook_signature(
        payload_body: bytes,
        signature: str
    ) -> bool:
        """
        Verify Paystack webhook signature.
        
        Args:
            payload_body: Raw request body
            signature: x-paystack-signature header value
            
        Returns:
            True if signature is valid
        """
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload_body,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
