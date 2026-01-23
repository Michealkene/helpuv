# backend/app/services/email_verifier.py
import smtplib
import dns.resolver
import re
import socket
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, update
import logging

from app.models.email import Email  # Assuming you have this model
from app.core.database import get_db

logger = logging.getLogger(__name__)


class EmailVerificationStatus:
    """Email verification status constants"""
    VALID = "valid"
    INVALID = "invalid"
    RISKY = "risky"
    UNKNOWN = "unknown"
    DISPOSABLE = "disposable"
    ROLE_BASED = "role_based"


class SMTPEmailVerifier:
    """SMTP-based email verification service"""
    
    # Common disposable email domains
    DISPOSABLE_DOMAINS = {
        'tempmail.com', 'guerrillamail.com', '10minutemail.com',
        'mailinator.com', 'throwaway.email', 'temp-mail.org',
        'fakeinbox.com', 'trashmail.com', 'yopmail.com'
    }
    
    # Role-based email prefixes
    ROLE_PREFIXES = {
        'info', 'admin', 'support', 'sales', 'help', 'contact',
        'service', 'noreply', 'no-reply', 'marketing', 'hello'
    }
    
    def __init__(self, from_email: str = "verify@helpuvio.com"):
        self.from_email = from_email
        
    def validate_email_format(self, email: str) -> bool:
        """Validate email format using regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def is_disposable(self, email: str) -> bool:
        """Check if email is from a disposable domain"""
        domain = email.split('@')[1].lower()
        return domain in self.DISPOSABLE_DOMAINS
    
    def is_role_based(self, email: str) -> bool:
        """Check if email is role-based"""
        local_part = email.split('@')[0].lower()
        return local_part in self.ROLE_PREFIXES
    
    def get_mx_records(self, domain: str) -> Optional[List[str]]:
        """Get MX records for domain"""
        try:
            records = dns.resolver.resolve(domain, 'MX')
            mx_hosts = [str(r.exchange).rstrip('.') for r in records]
            return sorted(mx_hosts, key=lambda x: dns.resolver.resolve(domain, 'MX')[0].preference)
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception) as e:
            logger.warning(f"No MX records found for {domain}: {e}")
            return None
    
    def verify_smtp(self, email: str, mx_host: str) -> Dict[str, any]:
        """Verify email via SMTP"""
        try:
            # Connect to mail server
            server = smtplib.SMTP(timeout=10)
            server.set_debuglevel(0)
            
            # Connect
            server.connect(mx_host, 25)
            server.helo(server.local_hostname)
            
            # Send MAIL FROM
            server.mail(self.from_email)
            
            # Send RCPT TO
            code, message = server.rcpt(email)
            server.quit()
            
            # 250 = success, 251 = user not local (still valid)
            if code in [250, 251]:
                return {
                    "valid": True,
                    "status": EmailVerificationStatus.VALID,
                    "smtp_code": code,
                    "message": message.decode() if isinstance(message, bytes) else str(message)
                }
            else:
                return {
                    "valid": False,
                    "status": EmailVerificationStatus.INVALID,
                    "smtp_code": code,
                    "message": message.decode() if isinstance(message, bytes) else str(message)
                }
                
        except smtplib.SMTPServerDisconnected:
            return {
                "valid": False,
                "status": EmailVerificationStatus.UNKNOWN,
                "error": "Server disconnected"
            }
        except smtplib.SMTPResponseException as e:
            return {
                "valid": False,
                "status": EmailVerificationStatus.INVALID,
                "smtp_code": e.smtp_code,
                "error": str(e)
            }
        except socket.timeout:
            return {
                "valid": None,
                "status": EmailVerificationStatus.UNKNOWN,
                "error": "Connection timeout"
            }
        except Exception as e:
            logger.error(f"SMTP verification error for {email}: {e}")
            return {
                "valid": None,
                "status": EmailVerificationStatus.UNKNOWN,
                "error": str(e)
            }
    
    def verify_email(self, email: str) -> Dict[str, any]:
        """
        Complete email verification process
        
        Returns:
            dict: {
                "email": str,
                "valid": bool,
                "status": str,
                "checks": dict,
                "verified_at": datetime
            }
        """
        result = {
            "email": email,
            "valid": False,
            "status": EmailVerificationStatus.INVALID,
            "checks": {},
            "verified_at": datetime.utcnow()
        }
        
        # 1. Format validation
        if not self.validate_email_format(email):
            result["checks"]["format"] = False
            result["status"] = EmailVerificationStatus.INVALID
            return result
        result["checks"]["format"] = True
        
        # 2. Disposable check
        if self.is_disposable(email):
            result["checks"]["disposable"] = True
            result["status"] = EmailVerificationStatus.DISPOSABLE
            return result
        result["checks"]["disposable"] = False
        
        # 3. Role-based check
        if self.is_role_based(email):
            result["checks"]["role_based"] = True
            result["status"] = EmailVerificationStatus.ROLE_BASED
            result["valid"] = True  # Role emails are valid but flagged
            return result
        result["checks"]["role_based"] = False
        
        # 4. MX record check
        domain = email.split('@')[1]
        mx_records = self.get_mx_records(domain)
        
        if not mx_records:
            result["checks"]["mx_records"] = False
            result["status"] = EmailVerificationStatus.INVALID
            return result
        result["checks"]["mx_records"] = True
        result["checks"]["mx_host"] = mx_records[0]
        
        # 5. SMTP verification
        smtp_result = self.verify_smtp(email, mx_records[0])
        result["checks"]["smtp"] = smtp_result
        result["valid"] = smtp_result.get("valid", False)
        result["status"] = smtp_result.get("status", EmailVerificationStatus.UNKNOWN)
        
        return result


class EmailVerificationService:
    """Service to verify emails in database"""
    
    def __init__(self, db: Session):
        self.db = db
        self.verifier = SMTPEmailVerifier()
    
    def verify_single_email(self, email_id: int) -> Dict[str, any]:
        """Verify a single email by ID"""
        email_record = self.db.query(Email).filter(Email.id == email_id).first()
        
        if not email_record:
            return {"error": "Email not found"}
        
        # Perform verification
        result = self.verifier.verify_email(email_record.email)
        
        # Update database
        email_record.verified = result["valid"]
        email_record.verification_status = result["status"]
        email_record.verified_at = result["verified_at"]
        
        self.db.commit()
        self.db.refresh(email_record)
        
        logger.info(f"Verified email {email_record.email}: {result['status']}")
        
        return {
            "email_id": email_id,
            "email": email_record.email,
            "result": result
        }
    
    def verify_unverified_emails(self, limit: int = 100) -> Dict[str, any]:
        """Verify all unverified emails (up to limit)"""
        unverified = self.db.query(Email).filter(
            Email.verified == False,
            Email.verification_status.is_(None)
        ).limit(limit).all()
        
        results = {
            "total": len(unverified),
            "verified": 0,
            "invalid": 0,
            "risky": 0,
            "unknown": 0,
            "emails": []
        }
        
        for email_record in unverified:
            result = self.verifier.verify_email(email_record.email)
            
            # Update database
            email_record.verified = result["valid"]
            email_record.verification_status = result["status"]
            email_record.verified_at = result["verified_at"]
            
            # Track stats
            if result["status"] == EmailVerificationStatus.VALID:
                results["verified"] += 1
            elif result["status"] == EmailVerificationStatus.INVALID:
                results["invalid"] += 1
            elif result["status"] in [EmailVerificationStatus.DISPOSABLE, EmailVerificationStatus.ROLE_BASED]:
                results["risky"] += 1
            else:
                results["unknown"] += 1
            
            results["emails"].append({
                "email": email_record.email,
                "status": result["status"]
            })
        
        self.db.commit()
        logger.info(f"Batch verification complete: {results}")
        
        return results
    
    def verify_company_emails(self, company_id: int) -> Dict[str, any]:
        """Verify all emails for a specific company"""
        emails = self.db.query(Email).filter(
            Email.company_id == company_id
        ).all()
        
        results = {
            "company_id": company_id,
            "total": len(emails),
            "verified": 0,
            "invalid": 0,
            "emails": []
        }
        
        for email_record in emails:
            result = self.verifier.verify_email(email_record.email)
            
            email_record.verified = result["valid"]
            email_record.verification_status = result["status"]
            email_record.verified_at = result["verified_at"]
            
            if result["valid"]:
                results["verified"] += 1
            else:
                results["invalid"] += 1
            
            results["emails"].append({
                "email": email_record.email,
                "status": result["status"]
            })
        
        self.db.commit()
        
        return results


# CLI tool for manual verification
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python email_verifier.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    verifier = SMTPEmailVerifier()
    result = verifier.verify_email(email)
    
    print(f"\n✉️  Email Verification Result for: {email}")
    print(f"Valid: {result['valid']}")
    print(f"Status: {result['status']}")
    print(f"\nChecks:")
    for check, value in result['checks'].items():
        print(f"  - {check}: {value}")