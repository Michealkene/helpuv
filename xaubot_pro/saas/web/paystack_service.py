"""Paystack payment integration for XAUBOT Pro SaaS"""
import os, requests, hmac, hashlib

PAYSTACK_SECRET = os.environ.get('PAYSTACK_SECRET_KEY', 'sk_test_xxx')
PAYSTACK_PUBLIC = os.environ.get('PAYSTACK_PUBLIC_KEY', 'pk_test_xxx')
BASE_URL = "https://api.paystack.co"
PLAN_AMOUNT = 9700  # $97 in kobo/cents
PLAN_CURRENCY = "USD"

def _headers():
    return {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
        "Content-Type": "application/json"
    }

def initialize_payment(email, user_id, ref_code=None, callback_url=None):
    """Start a $97 payment transaction"""
    payload = {
        "email": email,
        "amount": PLAN_AMOUNT,
        "currency": PLAN_CURRENCY,
        "reference": f"xaubot_{user_id}_{int(__import__('time').time())}",
        "callback_url": callback_url or "http://74.50.87.77/api/pay/paystack/verify",
        "metadata": {
            "user_id": user_id,
            "plan": "monthly",
            "ref_code": ref_code or ""
        }
    }
    r = requests.post(f"{BASE_URL}/transaction/initialize", json=payload, headers=_headers(), timeout=15)
    data = r.json()
    if data.get("status"):
        return {
            "success": True,
            "authorization_url": data["data"]["authorization_url"],
            "reference": data["data"]["reference"],
            "access_code": data["data"]["access_code"]
        }
    return {"success": False, "error": data.get("message", "Payment init failed")}

def verify_payment(reference):
    """Verify a completed payment"""
    r = requests.get(f"{BASE_URL}/transaction/verify/{reference}", headers=_headers(), timeout=15)
    data = r.json()
    if data.get("status") and data["data"]["status"] == "success":
        return {
            "success": True,
            "amount": data["data"]["amount"],
            "currency": data["data"]["currency"],
            "email": data["data"]["customer"]["email"],
            "reference": reference,
            "metadata": data["data"].get("metadata", {})
        }
    return {"success": False, "error": data.get("message", "Verification failed")}

def verify_webhook_signature(payload_body, signature):
    """Verify Paystack webhook is authentic"""
    expected = hmac.new(
        PAYSTACK_SECRET.encode('utf-8'),
        payload_body,
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
