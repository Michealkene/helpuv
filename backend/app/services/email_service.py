from typing import Optional
from app.core.config import settings
import httpx

class EmailService:
    """Email service using SendGrid or simple SMTP"""
    
    @staticmethod
    async def send_welcome_email(email: str, name: str):
        """Send welcome email to new user"""
        subject = "Welcome to Lead Marketplace"
        body = f"""
        Hi {name},
        
        Welcome to Lead Marketplace! We're excited to have you on board.
        
        Browse our datasets: {settings.FRONTEND_URL}/datasets
        
        Best regards,
        The Lead Marketplace Team
        """
        
        # TODO: Implement actual email sending
        print(f"[EMAIL] To: {email}, Subject: {subject}")
    
    @staticmethod
    async def send_purchase_receipt(email: str, dataset_name: str, amount: float, purchase_id: str):
        """Send purchase receipt email"""
        subject = f"Receipt for {dataset_name}"
        body = f"""
        Thank you for your purchase!
        
        Dataset: {dataset_name}
        Amount: ${amount:.2f}
        Order ID: {purchase_id}
        
        Download your dataset: {settings.FRONTEND_URL}/downloads
        
        Best regards,
        The Lead Marketplace Team
        """
        
        # TODO: Implement actual email sending
        print(f"[EMAIL] To: {email}, Subject: {subject}")
    
    @staticmethod
    async def send_refund_notification(email: str, dataset_name: str, amount: float):
        """Send refund notification email"""
        subject = "Refund Processed"
        body = f"""
        Your refund has been processed.
        
        Dataset: {dataset_name}
        Amount: ${amount:.2f}
        
        The refund will appear in your account within 5-10 business days.
        
        Best regards,
        The Lead Marketplace Team
        """
        
        # TODO: Implement actual email sending
        print(f"[EMAIL] To: {email}, Subject: {subject}")