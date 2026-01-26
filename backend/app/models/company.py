"""
Company model - Stores imported company lead data
"""

from sqlalchemy import (
    Column, String, Boolean, TIMESTAMP, Integer, Text, Float,
    text, ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
import enum


class EmailVerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    INVALID = "invalid"
    CATCH_ALL = "catch_all"
    UNKNOWN = "unknown"


class Company(Base):
    """
    Company model - stores imported lead data.
    Only companies with verified emails OR phone numbers are displayed.
    Companies with both email AND phone cost more.
    """
    __tablename__ = "companies"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core company info
    company_name = Column(String(500), nullable=False, index=True)
    category = Column(String(255), index=True)
    group_name = Column(String(255), index=True)  # "group" from CSV

    # Contact information
    email = Column(String(255), index=True)  # Primary email
    emails = Column(ARRAY(String), default=[])  # Additional emails from CSV
    phone = Column(String(100), index=True)  # Primary phone
    phones = Column(ARRAY(String), default=[])  # Additional phones from CSV

    # Address
    street = Column(String(500))
    locality = Column(String(255))  # City
    city = Column(String(255))  # Alias for locality
    state = Column(String(255), index=True)
    zip_code = Column(String(50))
    country = Column(String(100), index=True)

    # Online presence
    website = Column(String(500))
    linkedin_url = Column(String(500))
    twitter_url = Column(String(500))
    facebook_url = Column(String(500))
    instagram_url = Column(String(500))
    socials = Column(Text)  # Raw socials data from CSV

    # Business info
    ceo_name = Column(String(255))
    description = Column(Text)
    meta_title = Column(String(500))
    employee_count = Column(Integer)
    founded_year = Column(Integer)
    rating = Column(Float)
    reviews = Column(Integer)

    # Media
    avatar_url = Column(String(500))
    favicon_url = Column(String(500))

    # Crawl metadata
    performance_score = Column(Float)
    response_time_ms = Column(Integer)
    crawl_status = Column(String(50))
    crawl_error = Column(Text)
    sent = Column(Boolean, default=False)  # Whether email was sent

    # Email verification status
    email_verification_status = Column(
        SQLEnum(EmailVerificationStatus, values_callable=lambda x: [e.value for e in x]),
        default=EmailVerificationStatus.PENDING,
        index=True
    )
    email_verified_at = Column(TIMESTAMP(timezone=True))
    email_verification_error = Column(Text)
    email_mx_record = Column(String(255))
    email_smtp_response = Column(Text)

    # Enrichment level (for pricing)
    has_email = Column(Boolean, default=False, index=True)
    has_phone = Column(Boolean, default=False, index=True)
    has_verified_email = Column(Boolean, default=False, index=True)

    # Import tracking
    import_batch_id = Column(UUID(as_uuid=True), ForeignKey("import_batches.id"), index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), index=True)

    # Display control
    is_displayable = Column(Boolean, default=False, index=True)  # Only verified emails shown

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))

    # Relationships
    import_batch = relationship("ImportBatch", back_populates="companies")
    dataset = relationship("Dataset", back_populates="companies")

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_company_displayable_category', 'is_displayable', 'category'),
        Index('idx_company_displayable_country', 'is_displayable', 'country'),
        Index('idx_company_verification_status', 'email_verification_status'),
        Index('idx_company_has_email_phone', 'has_email', 'has_phone'),
    )

    def __repr__(self):
        return f"<Company {self.company_name}>"

    def update_displayable_status(self):
        """
        Update is_displayable based on verification rules:
        - Must have verified email OR phone number
        - If has email, it must be verified
        """
        if self.has_phone and not self.has_email:
            # Phone only - displayable
            self.is_displayable = True
        elif self.has_email and self.email_verification_status == EmailVerificationStatus.VERIFIED:
            # Has verified email - displayable
            self.is_displayable = True
            self.has_verified_email = True
        else:
            # Has unverified email without phone, or pending verification
            self.is_displayable = False
            self.has_verified_email = False


class ImportBatch(Base):
    """
    Tracks CSV import batches for auditing and rollback.
    """
    __tablename__ = "import_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Import info
    filename = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer)
    total_rows = Column(Integer, default=0)
    imported_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    skipped_rows = Column(Integer, default=0)

    # Verification stats
    verified_emails = Column(Integer, default=0)
    invalid_emails = Column(Integer, default=0)
    pending_verification = Column(Integer, default=0)

    # Status
    status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    error_message = Column(Text)
    error_details = Column(JSONB)  # Detailed error info per row

    # Admin who triggered import
    imported_by = Column(UUID(as_uuid=True), ForeignKey("admin_users.id"))

    # Target dataset (optional)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))

    # Timestamps
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))

    # Relationships
    companies = relationship("Company", back_populates="import_batch")
    admin = relationship("AdminUser")
    dataset = relationship("Dataset")

    def __repr__(self):
        return f"<ImportBatch {self.filename} - {self.status}>"


class EmailVerificationJob(Base):
    """
    Queue for email verification jobs processed by workers.
    """
    __tablename__ = "email_verification_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Target
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False)

    # Job status
    status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)

    # Results
    result = Column(String(50))  # verified, invalid, catch_all, unknown
    error_message = Column(Text)
    mx_record = Column(String(255))
    smtp_response = Column(Text)

    # Worker tracking
    worker_id = Column(String(100))
    locked_at = Column(TIMESTAMP(timezone=True))

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    processed_at = Column(TIMESTAMP(timezone=True))

    # Relationship
    company = relationship("Company")

    __table_args__ = (
        Index('idx_job_status_created', 'status', 'created_at'),
    )

    def __repr__(self):
        return f"<EmailVerificationJob {self.email} - {self.status}>"
