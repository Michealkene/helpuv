# backend/app/routers/email_verification.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.services.email_verifier import EmailVerificationService
from app.models.email import Email

router = APIRouter(tags=["Email Verification"])


# Pydantic schemas
class EmailVerifyRequest(BaseModel):
    email: EmailStr


class EmailVerifyResponse(BaseModel):
    email_id: int
    email: str
    valid: bool
    status: str
    verified_at: Optional[str]


class BatchVerifyResponse(BaseModel):
    total: int
    verified: int
    invalid: int
    risky: int
    unknown: int


class CompanyEmailsResponse(BaseModel):
    company_id: int
    total: int
    verified: int
    invalid: int


# Routes
@router.post("/verify-email", response_model=EmailVerifyResponse)
async def verify_single_email(
    email_id: int,
    db: Session = Depends(get_db)
):
    """
    Verify a single email by ID
    
    This performs SMTP verification and updates the database
    """
    service = EmailVerificationService(db)
    result = service.verify_single_email(email_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return {
        "email_id": result["email_id"],
        "email": result["email"],
        "valid": result["result"]["valid"],
        "status": result["result"]["status"],
        "verified_at": str(result["result"]["verified_at"])
    }


@router.post("/verify-batch", response_model=BatchVerifyResponse)
async def verify_batch(
    background_tasks: BackgroundTasks,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Verify unverified emails in batch
    
    Parameters:
    - limit: Maximum number of emails to verify (default: 100)
    
    This runs as a background task to avoid timeout
    """
    service = EmailVerificationService(db)
    
    # Run in background
    background_tasks.add_task(service.verify_unverified_emails, limit)
    
    return {
        "total": limit,
        "verified": 0,
        "invalid": 0,
        "risky": 0,
        "unknown": 0,
        "message": "Verification started in background"
    }


@router.post("/verify-company/{company_id}", response_model=CompanyEmailsResponse)
async def verify_company_emails(
    company_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Verify all emails for a specific company
    """
    service = EmailVerificationService(db)
    
    # Check if company exists
    from app.models.company import Company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Run verification
    background_tasks.add_task(service.verify_company_emails, company_id)
    
    return {
        "company_id": company_id,
        "total": 0,
        "verified": 0,
        "invalid": 0,
        "message": "Verification started in background"
    }


@router.get("/verification-stats")
async def get_verification_stats(db: Session = Depends(get_db)):
    """Get email verification statistics"""
    from sqlalchemy import func
    
    stats = db.query(
        Email.verification_status,
        func.count(Email.id).label('count')
    ).group_by(Email.verification_status).all()
    
    total = db.query(func.count(Email.id)).scalar()
    verified_count = db.query(func.count(Email.id)).filter(Email.verified == True).scalar()
    unverified_count = db.query(func.count(Email.id)).filter(Email.verified == False).scalar()
    
    return {
        "total_emails": total,
        "verified": verified_count,
        "unverified": unverified_count,
        "by_status": {
            status: count for status, count in stats if status is not None
        }
    }


@router.get("/unverified-emails")
async def get_unverified_emails(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get list of unverified emails"""
    emails = db.query(Email).filter(
        Email.verified == False
    ).offset(offset).limit(limit).all()
    
    return {
        "emails": [
            {
                "id": e.id,
                "email": e.email,
                "company_id": e.company_id,
                "source": e.source,
                "created_at": str(e.created_at)
            }
            for e in emails
        ],
        "total": len(emails)
    }