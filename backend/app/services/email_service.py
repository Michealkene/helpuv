"""
Email Service - Send transactional emails via SendGrid
"""

import httpx
from typing import Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending transactional emails.
    
    Uses SendGrid API for delivery.
    """
    
    SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"
    
    def __init__(self):
        self.api_key = settings.SENDGRID_API_KEY
        self.from_email = settings.FROM_EMAIL
        self.is_configured = bool(self.api_key)
        
        if not self.is_configured:
            logger.warning("Email service not configured - SENDGRID_API_KEY missing")
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via SendGrid.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback (optional)
            
        Returns:
            True if sent successfully
        """
        if not self.is_configured:
            logger.warning(f"Email not sent (not configured): {subject} -> {to_email}")
            return False
        
        content = [{"type": "text/html", "value": html_content}]
        if text_content:
            content.insert(0, {"type": "text/plain", "value": text_content})
        
        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": self.from_email, "name": "Helpuvio"},
            "subject": subject,
            "content": content
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.SENDGRID_URL,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                if response.status_code in [200, 201, 202]:
                    logger.info(f"Email sent: {subject} -> {to_email}")
                    return True
                else:
                    logger.error(f"SendGrid error: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to send email: {e}")
                return False
    
    async def send_welcome_email(self, email: str, name: str) -> bool:
        """Send welcome email after signup"""
        subject = "Welcome to Helpuvio!"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #0066FF;">Welcome to Helpuvio!</h1>
            <p>Hi {name},</p>
            <p>Thank you for signing up! You now have access to our B2B lead data marketplace.</p>
            <p>Browse our datasets to find the perfect leads for your business:</p>
            <p style="margin: 20px 0;">
                <a href="{settings.FRONTEND_URL}/datasets" 
                   style="background-color: #0066FF; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px;">
                    Browse Datasets
                </a>
            </p>
            <p>If you have any questions, reply to this email.</p>
            <p>Best,<br>The Helpuvio Team</p>
        </div>
        """
        return await self._send_email(email, subject, html_content)

    async def send_verify_email(self, email: str, name: str, verify_token: str) -> bool:
        """Send email verification email after signup"""
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={verify_token}"
        subject = "Verify your email address"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #0066FF;">Verify Your Email</h1>
            <p>Hi {name},</p>
            <p>Thank you for signing up! Please verify your email address by clicking the button below:</p>

            <p style="margin: 20px 0;">
                <a href="{verify_url}"
                   style="background-color: #0066FF; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px;">
                    Verify Email
                </a>
            </p>

            <p style="color: #666; font-size: 14px;">
                This link will expire in 24 hours. If you didn't create an account, you can safely ignore this email.
            </p>

            <p>Best,<br>The Helpuvio Team</p>
        </div>
        """
        return await self._send_email(email, subject, html_content)

    async def send_purchase_receipt(
        self,
        email: str,
        name: str,
        dataset_name: str,
        amount_cents: int,
        purchase_id: str
    ) -> bool:
        """Send purchase receipt email"""
        amount_display = f"${amount_cents / 100:.2f}"
        subject = f"Your purchase: {dataset_name}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #0066FF;">Thank you for your purchase!</h1>
            <p>Hi {name},</p>
            <p>Your purchase was successful. Here are the details:</p>
            
            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0;"><strong>Dataset:</strong> {dataset_name}</p>
                <p style="margin: 10px 0 0;"><strong>Amount:</strong> {amount_display}</p>
                <p style="margin: 10px 0 0;"><strong>Order ID:</strong> {purchase_id}</p>
            </div>
            
            <p>Download your CSV file now:</p>
            <p style="margin: 20px 0;">
                <a href="{settings.FRONTEND_URL}/downloads" 
                   style="background-color: #0066FF; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px;">
                    Download CSV
                </a>
            </p>
            
            <p style="color: #666; font-size: 14px;">
                You can re-download your files anytime from your Downloads page.
            </p>
            
            <p>Best,<br>The Helpuvio Team</p>
        </div>
        """
        return await self._send_email(email, subject, html_content)
    
    async def send_refund_confirmation(
        self,
        email: str,
        name: str,
        dataset_name: str,
        amount_cents: int,
        reason: str
    ) -> bool:
        """Send refund confirmation email"""
        amount_display = f"${amount_cents / 100:.2f}"
        subject = f"Refund processed: {dataset_name}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #0066FF;">Refund Processed</h1>
            <p>Hi {name},</p>
            <p>Your refund has been processed. Here are the details:</p>
            
            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0;"><strong>Dataset:</strong> {dataset_name}</p>
                <p style="margin: 10px 0 0;"><strong>Refund Amount:</strong> {amount_display}</p>
                <p style="margin: 10px 0 0;"><strong>Reason:</strong> {reason}</p>
            </div>
            
            <p>The refund will appear in your account within 5-10 business days.</p>
            
            <p>If you have any questions, reply to this email.</p>
            
            <p>Best,<br>The Helpuvio Team</p>
        </div>
        """
        return await self._send_email(email, subject, html_content)
    
    async def send_password_reset(
        self,
        email: str,
        name: str,
        reset_token: str
    ) -> bool:
        """Send password reset email"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        subject = "Reset your password"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #0066FF;">Reset Your Password</h1>
            <p>Hi {name},</p>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            
            <p style="margin: 20px 0;">
                <a href="{reset_url}" 
                   style="background-color: #0066FF; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px;">
                    Reset Password
                </a>
            </p>
            
            <p style="color: #666; font-size: 14px;">
                This link will expire in 1 hour. If you didn't request this, you can safely ignore this email.
            </p>
            
            <p>Best,<br>The Helpuvio Team</p>
        </div>
        """
        return await self._send_email(email, subject, html_content)
