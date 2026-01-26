class PaymentService:
    @staticmethod
    async def create_payment_link(email: str, amount_cents: int, reference: str) -> dict:
        """Create Paystack payment link - implement with actual Paystack API"""
        return {
            "authorization_url": f"https://checkout.paystack.com/{reference}",
            "reference": reference
        }
    
    @staticmethod
    async def verify_payment(reference: str) -> dict:
        """Verify Paystack payment - implement with actual Paystack API"""
        return {
            "status": "success",
            "amount": 0
        }