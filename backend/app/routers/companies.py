"""
Companies Router - CSV Import, Company Browsing, and Email Verification
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime
from typing import List, Optional
from uuid import UUID
import asyncio

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.models.admin import AdminUser
from app.models.user import User
from app.models.company import Company, ImportBatch, EmailVerificationJob, EmailVerificationStatus
from app.schemas.company import (
    CompanyResponse,
    CompanyDetailResponse,
    CompanyListResponse,
    CompanyAdminListResponse,
    ImportBatchCreate,
    ImportBatchResponse,
    ImportBatchListResponse,
    ImportProgressResponse,
    BulkVerificationRequest,
    BulkVerificationResponse,
    VerificationStatsResponse,
    WorkerStatusResponse
)
from app.services.csv_importer import CSVImporter, ImportStatsService
from app.services.email_verifier import (
    SMTPEmailVerifier,
    VerificationManager,
    get_verification_manager
)

router = APIRouter()


# ============================================================
# Public Company Endpoints (for customers)
# ============================================================

@router.get("/", response_model=CompanyListResponse)
async def list_companies(
    category: Optional[str] = Query(None, description="Filter by category"),
    country: Optional[str] = Query(None, description="Filter by country"),
    state: Optional[str] = Query(None, description="Filter by state"),
    group: Optional[str] = Query(None, description="Filter by group"),
    has_email: Optional[bool] = Query(None, description="Filter by has email"),
    has_phone: Optional[bool] = Query(None, description="Filter by has phone"),
    search: Optional[str] = Query(None, description="Search company names"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List displayable companies (verified emails only).
    Companies without verified email OR phone are hidden.
    """
    query = db.query(Company).filter(Company.is_displayable == True)

    # Apply filters
    if category:
        query = query.filter(Company.category == category)
    if country:
        query = query.filter(Company.country == country)
    if state:
        query = query.filter(Company.state == state)
    if group:
        query = query.filter(Company.group_name == group)
    if has_email is not None:
        query = query.filter(Company.has_verified_email == has_email)
    if has_phone is not None:
        query = query.filter(Company.has_phone == has_phone)
    if search:
        query = query.filter(Company.company_name.ilike(f"%{search}%"))

    # Get total count
    total = query.count()
    total_pages = (total + page_size - 1) // page_size

    # Get paginated results
    companies = query.order_by(Company.company_name).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    items = [
        CompanyResponse(
            id=c.id,
            company_name=c.company_name,
            category=c.category,
            group_name=c.group_name,
            email=c.email if c.has_verified_email else None,  # Only show verified emails
            emails=c.emails if c.has_verified_email else [],
            phone=c.phone,
            phones=c.phones,
            street=c.street,
            locality=c.locality,
            city=c.city,
            state=c.state,
            zip_code=c.zip_code,
            country=c.country,
            website=c.website,
            linkedin_url=c.linkedin_url,
            twitter_url=c.twitter_url,
            facebook_url=c.facebook_url,
            instagram_url=c.instagram_url,
            ceo_name=c.ceo_name,
            description=c.description,
            employee_count=c.employee_count,
            founded_year=c.founded_year,
            rating=c.rating,
            reviews=c.reviews,
            has_email=c.has_verified_email,
            has_phone=c.has_phone,
            has_verified_email=c.has_verified_email,
            is_displayable=c.is_displayable,
            created_at=c.created_at
        )
        for c in companies
    ]

    return CompanyListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/categories", response_model=List[dict])
async def list_categories(db: Session = Depends(get_db)):
    """Get list of all categories with company counts"""
    categories = db.query(
        Company.category,
        func.count(Company.id).label("count")
    ).filter(
        Company.is_displayable == True,
        Company.category != None
    ).group_by(Company.category).order_by(func.count(Company.id).desc()).all()

    return [{"name": cat, "count": count} for cat, count in categories if cat]


@router.get("/countries", response_model=List[dict])
async def list_countries(db: Session = Depends(get_db)):
    """Get list of all countries with company counts"""
    countries = db.query(
        Company.country,
        func.count(Company.id).label("count")
    ).filter(
        Company.is_displayable == True,
        Company.country != None
    ).group_by(Company.country).order_by(func.count(Company.id).desc()).all()

    return [{"name": country, "count": count} for country, count in countries if country]


@router.get("/groups", response_model=List[dict])
async def list_groups(db: Session = Depends(get_db)):
    """Get list of all groups with company counts"""
    groups = db.query(
        Company.group_name,
        func.count(Company.id).label("count")
    ).filter(
        Company.is_displayable == True,
        Company.group_name != None
    ).group_by(Company.group_name).order_by(func.count(Company.id).desc()).all()

    return [{"name": grp, "count": count} for grp, count in groups if grp]


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a single company by ID (must be displayable)"""
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.is_displayable == True
    ).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return CompanyResponse(
        id=company.id,
        company_name=company.company_name,
        category=company.category,
        group_name=company.group_name,
        email=company.email if company.has_verified_email else None,
        emails=company.emails if company.has_verified_email else [],
        phone=company.phone,
        phones=company.phones,
        street=company.street,
        locality=company.locality,
        city=company.city,
        state=company.state,
        zip_code=company.zip_code,
        country=company.country,
        website=company.website,
        linkedin_url=company.linkedin_url,
        twitter_url=company.twitter_url,
        facebook_url=company.facebook_url,
        instagram_url=company.instagram_url,
        ceo_name=company.ceo_name,
        description=company.description,
        employee_count=company.employee_count,
        founded_year=company.founded_year,
        rating=company.rating,
        reviews=company.reviews,
        has_email=company.has_verified_email,
        has_phone=company.has_phone,
        has_verified_email=company.has_verified_email,
        is_displayable=company.is_displayable,
        created_at=company.created_at
    )


# ============================================================
# Admin Company Endpoints
# ============================================================

@router.get("/admin/all", response_model=CompanyAdminListResponse)
async def admin_list_companies(
    category: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    batch_id: Optional[UUID] = Query(None),
    is_displayable: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Admin view of all companies (including unverified).
    """
    query = db.query(Company)

    # Apply filters
    if category:
        query = query.filter(Company.category == category)
    if country:
        query = query.filter(Company.country == country)
    if state:
        query = query.filter(Company.state == state)
    if verification_status:
        query = query.filter(Company.email_verification_status == verification_status)
    if batch_id:
        query = query.filter(Company.import_batch_id == batch_id)
    if is_displayable is not None:
        query = query.filter(Company.is_displayable == is_displayable)
    if search:
        query = query.filter(
            or_(
                Company.company_name.ilike(f"%{search}%"),
                Company.email.ilike(f"%{search}%")
            )
        )

    total = query.count()
    total_pages = (total + page_size - 1) // page_size

    companies = query.order_by(Company.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # Get verification stats
    stats_service = ImportStatsService(db)
    verification_stats = stats_service.get_verification_stats(batch_id)

    items = [
        CompanyDetailResponse(
            id=c.id,
            company_name=c.company_name,
            category=c.category,
            group_name=c.group_name,
            email=c.email,
            emails=c.emails or [],
            phone=c.phone,
            phones=c.phones or [],
            street=c.street,
            locality=c.locality,
            city=c.city,
            state=c.state,
            zip_code=c.zip_code,
            country=c.country,
            website=c.website,
            linkedin_url=c.linkedin_url,
            twitter_url=c.twitter_url,
            facebook_url=c.facebook_url,
            instagram_url=c.instagram_url,
            ceo_name=c.ceo_name,
            description=c.description,
            employee_count=c.employee_count,
            founded_year=c.founded_year,
            rating=c.rating,
            reviews=c.reviews,
            has_email=c.has_email,
            has_phone=c.has_phone,
            has_verified_email=c.has_verified_email,
            is_displayable=c.is_displayable,
            email_verification_status=c.email_verification_status,
            email_verified_at=c.email_verified_at,
            email_verification_error=c.email_verification_error,
            email_mx_record=c.email_mx_record,
            import_batch_id=c.import_batch_id,
            dataset_id=c.dataset_id,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in companies
    ]

    return CompanyAdminListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        verification_stats=verification_stats
    )


@router.delete("/admin/{company_id}")
async def delete_company(
    company_id: UUID,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a company"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Delete associated verification jobs
    db.query(EmailVerificationJob).filter(
        EmailVerificationJob.company_id == company_id
    ).delete()

    db.delete(company)
    db.commit()

    return {"message": "Company deleted"}


# ============================================================
# CSV Import Endpoints
# ============================================================

@router.post("/admin/import", response_model=ImportBatchResponse, status_code=status.HTTP_201_CREATED)
async def import_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dataset_id: Optional[int] = Query(None),
    auto_verify: bool = Query(True, description="Start email verification automatically"),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Import companies from CSV file.

    Expected CSV format:
    category,state,company,phone,street,locality,state,zip,website,rating,reviews,
    sent,email,emails,phones,socials,linkedin_url,twitter_url,facebook_url,
    instagram_url,ceo_name,description,meta_title,avatar_url,favicon_url,
    employee_count,founded_year,performance_score,response_time_ms,crawl_status,
    crawl_error,country,group

    Rules:
    - Only companies with email OR phone are imported
    - Companies with unverified emails are hidden until verified
    - Companies with both email AND phone are marked as premium
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        importer = CSVImporter(db)
        batch = await importer.import_csv(
            file=file.file,
            filename=file.filename,
            admin_id=admin.id,
            dataset_id=dataset_id,
            auto_verify=auto_verify
        )

        # Start verification workers in background if auto_verify
        if auto_verify and batch.pending_verification > 0:
            background_tasks.add_task(
                start_verification_for_batch,
                db,
                batch.id
            )

        return ImportBatchResponse(
            id=batch.id,
            filename=batch.filename,
            file_size_bytes=batch.file_size_bytes,
            total_rows=batch.total_rows,
            imported_rows=batch.imported_rows,
            failed_rows=batch.failed_rows,
            skipped_rows=batch.skipped_rows,
            verified_emails=batch.verified_emails,
            invalid_emails=batch.invalid_emails,
            pending_verification=batch.pending_verification,
            status=batch.status,
            error_message=batch.error_message,
            started_at=batch.started_at,
            completed_at=batch.completed_at,
            created_at=batch.created_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/admin/imports", response_model=ImportBatchListResponse)
async def list_imports(
    status_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all import batches"""
    query = db.query(ImportBatch)

    if status_filter:
        query = query.filter(ImportBatch.status == status_filter)

    total = query.count()
    total_pages = (total + page_size - 1) // page_size

    batches = query.order_by(ImportBatch.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    items = [
        ImportBatchResponse(
            id=b.id,
            filename=b.filename,
            file_size_bytes=b.file_size_bytes,
            total_rows=b.total_rows,
            imported_rows=b.imported_rows,
            failed_rows=b.failed_rows,
            skipped_rows=b.skipped_rows,
            verified_emails=b.verified_emails,
            invalid_emails=b.invalid_emails,
            pending_verification=b.pending_verification,
            status=b.status,
            error_message=b.error_message,
            started_at=b.started_at,
            completed_at=b.completed_at,
            created_at=b.created_at
        )
        for b in batches
    ]

    return ImportBatchListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/admin/imports/{batch_id}", response_model=ImportBatchResponse)
async def get_import(
    batch_id: UUID,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get import batch details"""
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")

    return ImportBatchResponse(
        id=batch.id,
        filename=batch.filename,
        file_size_bytes=batch.file_size_bytes,
        total_rows=batch.total_rows,
        imported_rows=batch.imported_rows,
        failed_rows=batch.failed_rows,
        skipped_rows=batch.skipped_rows,
        verified_emails=batch.verified_emails,
        invalid_emails=batch.invalid_emails,
        pending_verification=batch.pending_verification,
        status=batch.status,
        error_message=batch.error_message,
        started_at=batch.started_at,
        completed_at=batch.completed_at,
        created_at=batch.created_at
    )


@router.get("/admin/imports/{batch_id}/progress", response_model=ImportProgressResponse)
async def get_import_progress(
    batch_id: UUID,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get real-time import and verification progress"""
    stats_service = ImportStatsService(db)
    progress = stats_service.get_batch_progress(batch_id)

    if not progress:
        raise HTTPException(status_code=404, detail="Import batch not found")

    return ImportProgressResponse(**progress)


@router.delete("/admin/imports/{batch_id}")
async def delete_import(
    batch_id: UUID,
    delete_companies: bool = Query(True, description="Also delete imported companies"),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete an import batch and optionally all its companies"""
    batch = db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")

    if delete_companies:
        # Delete verification jobs for companies in this batch
        db.query(EmailVerificationJob).filter(
            EmailVerificationJob.company_id.in_(
                db.query(Company.id).filter(Company.import_batch_id == batch_id)
            )
        ).delete(synchronize_session=False)

        # Delete companies
        db.query(Company).filter(Company.import_batch_id == batch_id).delete()

    db.delete(batch)
    db.commit()

    return {"message": "Import batch deleted"}


# ============================================================
# Email Verification Endpoints
# ============================================================

@router.post("/admin/verify", response_model=BulkVerificationResponse)
async def start_verification(
    request: BulkVerificationRequest,
    background_tasks: BackgroundTasks,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Start bulk email verification.

    If neither company_ids nor batch_id specified, verifies all pending emails.
    """
    manager = get_verification_manager(db)

    # Queue verification jobs
    jobs_queued = manager.queue_verification(
        company_ids=request.company_ids,
        batch_id=request.batch_id
    )

    if jobs_queued == 0:
        return BulkVerificationResponse(
            job_id=UUID(int=0),
            total_emails=0,
            status="no_pending",
            message="No pending emails to verify"
        )

    # Start workers in background
    background_tasks.add_task(
        run_verification_workers,
        db,
        num_workers=min(3, (jobs_queued // 100) + 1),
        max_concurrent=request.max_concurrent
    )

    return BulkVerificationResponse(
        job_id=UUID(int=1),
        total_emails=jobs_queued,
        status="started",
        message=f"Started verification for {jobs_queued} emails"
    )


@router.get("/admin/verify/stats", response_model=VerificationStatsResponse)
async def get_verification_stats(
    batch_id: Optional[UUID] = Query(None),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get email verification statistics"""
    stats_service = ImportStatsService(db)
    stats = stats_service.get_verification_stats(batch_id)
    return VerificationStatsResponse(**stats)


@router.get("/admin/verify/workers", response_model=WorkerStatusResponse)
async def get_worker_status(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get status of verification workers"""
    manager = get_verification_manager(db)
    status = manager.get_worker_status()
    return WorkerStatusResponse(**status)


@router.post("/admin/verify/stop")
async def stop_verification(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Stop all verification workers"""
    manager = get_verification_manager(db)
    manager.stop_workers()
    return {"message": "Verification workers stopped"}


# ============================================================
# Helper Functions
# ============================================================

async def start_verification_for_batch(db: Session, batch_id: UUID):
    """Background task to start verification for a batch"""
    manager = get_verification_manager(db)
    manager.queue_verification(batch_id=batch_id)
    await manager.start_workers(num_workers=3, max_concurrent_per_worker=10)


async def run_verification_workers(db: Session, num_workers: int = 3, max_concurrent: int = 10):
    """Background task to run verification workers"""
    manager = get_verification_manager(db)
    await manager.start_workers(num_workers=num_workers, max_concurrent_per_worker=max_concurrent)
