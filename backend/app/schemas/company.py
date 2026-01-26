"""
Company schemas for API validation and serialization
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class EmailVerificationStatusEnum(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    INVALID = "invalid"
    CATCH_ALL = "catch_all"
    UNKNOWN = "unknown"


# ============================================================
# Company Schemas
# ============================================================

class CompanyBase(BaseModel):
    """Base company fields"""
    company_name: str
    category: Optional[str] = None
    group_name: Optional[str] = None

    # Contact
    email: Optional[str] = None
    emails: Optional[List[str]] = []
    phone: Optional[str] = None
    phones: Optional[List[str]] = []

    # Address
    street: Optional[str] = None
    locality: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None

    # Online
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None

    # Business
    ceo_name: Optional[str] = None
    description: Optional[str] = None
    employee_count: Optional[int] = None
    founded_year: Optional[int] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None


class CompanyCreate(CompanyBase):
    """Schema for creating a company"""
    pass


class CompanyResponse(CompanyBase):
    """Company response for public API"""
    id: UUID
    has_email: bool
    has_phone: bool
    has_verified_email: bool
    is_displayable: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyDetailResponse(CompanyResponse):
    """Detailed company response for admin"""
    email_verification_status: EmailVerificationStatusEnum
    email_verified_at: Optional[datetime] = None
    email_verification_error: Optional[str] = None
    email_mx_record: Optional[str] = None
    import_batch_id: Optional[UUID] = None
    dataset_id: Optional[int] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    """Paginated company list"""
    items: List[CompanyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CompanyAdminListResponse(BaseModel):
    """Paginated company list for admin"""
    items: List[CompanyDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    verification_stats: dict


# ============================================================
# Import Batch Schemas
# ============================================================

class ImportBatchCreate(BaseModel):
    """Schema for starting an import"""
    dataset_id: Optional[int] = None
    auto_verify: bool = True  # Start verification automatically


class ImportBatchResponse(BaseModel):
    """Import batch response"""
    id: UUID
    filename: str
    file_size_bytes: Optional[int] = None
    total_rows: int
    imported_rows: int
    failed_rows: int
    skipped_rows: int
    verified_emails: int
    invalid_emails: int
    pending_verification: int
    status: str
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ImportBatchListResponse(BaseModel):
    """Paginated import batch list"""
    items: List[ImportBatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ImportProgressResponse(BaseModel):
    """Real-time import progress"""
    batch_id: UUID
    status: str
    total_rows: int
    imported_rows: int
    failed_rows: int
    progress_percent: float
    current_phase: str  # "importing", "verifying", "completed"
    verification_progress: Optional[dict] = None


# ============================================================
# Email Verification Schemas
# ============================================================

class EmailVerificationRequest(BaseModel):
    """Request to verify a single email"""
    email: str


class EmailVerificationResult(BaseModel):
    """Result of email verification"""
    email: str
    status: EmailVerificationStatusEnum
    mx_record: Optional[str] = None
    smtp_response: Optional[str] = None
    error: Optional[str] = None
    verified_at: Optional[datetime] = None


class BulkVerificationRequest(BaseModel):
    """Request to verify multiple emails"""
    company_ids: Optional[List[UUID]] = None  # If None, verify all pending
    batch_id: Optional[UUID] = None  # Verify all in batch
    max_concurrent: int = Field(default=10, ge=1, le=50)


class BulkVerificationResponse(BaseModel):
    """Response for bulk verification start"""
    job_id: UUID
    total_emails: int
    status: str
    message: str


class VerificationStatsResponse(BaseModel):
    """Verification statistics"""
    total_companies: int
    total_with_email: int
    verified: int
    invalid: int
    catch_all: int
    pending: int
    unknown: int
    verification_rate: float


# ============================================================
# CSV Import Column Mapping
# ============================================================

CSV_COLUMN_MAPPING = {
    "category": "category",
    "state": "state",
    "company": "company_name",
    "phone": "phone",
    "street": "street",
    "locality": "locality",
    "zip": "zip_code",
    "website": "website",
    "rating": "rating",
    "reviews": "reviews",
    "sent": "sent",
    "email": "email",
    "emails": "emails",
    "phones": "phones",
    "socials": "socials",
    "linkedin_url": "linkedin_url",
    "twitter_url": "twitter_url",
    "facebook_url": "facebook_url",
    "instagram_url": "instagram_url",
    "ceo_name": "ceo_name",
    "description": "description",
    "meta_title": "meta_title",
    "avatar_url": "avatar_url",
    "favicon_url": "favicon_url",
    "employee_count": "employee_count",
    "founded_year": "founded_year",
    "performance_score": "performance_score",
    "response_time_ms": "response_time_ms",
    "crawl_status": "crawl_status",
    "crawl_error": "crawl_error",
    "country": "country",
    "group": "group_name",
}


# ============================================================
# Worker Schemas
# ============================================================

class WorkerStatusResponse(BaseModel):
    """Status of verification workers"""
    total_workers: int
    active_workers: int
    jobs_pending: int
    jobs_processing: int
    jobs_completed_today: int
    avg_verification_time_ms: Optional[float] = None
