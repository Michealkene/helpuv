"""
Admin Router - Dashboard, dataset management, and user management
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import List, Optional
import uuid
import re
import csv
import io
import json

from app.core.database import get_db
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_admin
from app.models.admin import AdminUser, AdminAuditLog, DailyMetric
from app.models.dataset import Dataset, Category, DatasetField
from app.models.purchase import Purchase, DownloadLog
from app.models.user import User
from app.schemas.admin import (
    AdminLogin,
    AdminCreate,
    AdminResponse,
    AdminAuthResponse,
    DashboardStats,
    DashboardResponse,
    UserAdminResponse,
    PaginatedUserResponse,
    UserStatusUpdate
)
from app.schemas.dataset import (
    DatasetCreate,
    DatasetUpdate,
    DatasetAdminResponse,
    CategoryResponse
)
from app.schemas.purchase import (
    PurchaseDetailResponse,
    RefundRequest,
    PaginatedPurchaseDetailResponse
)
from app.services.storage_service import StorageService
from app.services.payment_service import PaymentService
from app.services.email_service import EmailService

router = APIRouter(prefix="/admin", tags=["admin"])


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a name"""
    slug = name.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug.strip('-')


async def log_admin_action(
    db: Session,
    admin_id: str,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    details: dict = None,
    ip_address: str = None
):
    """Log an admin action for audit trail"""
    log = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()


# ============================================================
# Admin Authentication
# ============================================================

@router.post("/login", response_model=AdminAuthResponse)
async def admin_login(
    credentials: AdminLogin,
    db: Session = Depends(get_db)
):
    """
    Admin login - separate from regular user login.
    """
    admin = db.query(AdminUser).filter(
        AdminUser.email == credentials.email.lower()
    ).first()
    
    if not admin or not verify_password(credentials.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    admin.last_login_at = datetime.utcnow()
    db.commit()
    
    # Generate token with admin role
    access_token = create_access_token({
        "sub": str(admin.id),
        "email": admin.email,
        "role": "admin"
    })
    
    return AdminAuthResponse(
        access_token=access_token,
        admin=AdminResponse(
            id=str(admin.id),
            email=admin.email,
            name=admin.name,
            role=admin.role,
            is_active=admin.is_active,
            created_at=admin.created_at,
            last_login_at=admin.last_login_at
        )
    )


# ============================================================
# Dashboard
# ============================================================

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get admin dashboard data.
    """
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    
    # Total stats
    total_revenue = db.query(func.sum(Purchase.amount_cents)).filter(
        Purchase.status == "paid"
    ).scalar() or 0
    
    total_purchases = db.query(Purchase).filter(Purchase.status == "paid").count()
    total_users = db.query(User).count()
    total_datasets = db.query(Dataset).count()
    
    # This month stats
    revenue_this_month = db.query(func.sum(Purchase.amount_cents)).filter(
        Purchase.status == "paid",
        Purchase.paid_at >= month_start
    ).scalar() or 0
    
    purchases_this_month = db.query(Purchase).filter(
        Purchase.status == "paid",
        Purchase.paid_at >= month_start
    ).count()
    
    signups_this_month = db.query(User).filter(
        User.created_at >= month_start
    ).count()
    
    # Last month for comparison
    revenue_last_month = db.query(func.sum(Purchase.amount_cents)).filter(
        Purchase.status == "paid",
        Purchase.paid_at >= last_month_start,
        Purchase.paid_at < month_start
    ).scalar() or 0
    
    # Calculate change percentages
    revenue_change = None
    if revenue_last_month > 0:
        revenue_change = ((revenue_this_month - revenue_last_month) / revenue_last_month) * 100
    
    # Revenue chart (last 30 days)
    revenue_chart = []
    for i in range(30):
        date = (now - timedelta(days=29-i)).date()
        day_start = datetime.combine(date, datetime.min.time())
        day_end = datetime.combine(date, datetime.max.time())
        
        day_revenue = db.query(func.sum(Purchase.amount_cents)).filter(
            Purchase.status == "paid",
            Purchase.paid_at >= day_start,
            Purchase.paid_at <= day_end
        ).scalar() or 0
        
        day_purchases = db.query(Purchase).filter(
            Purchase.status == "paid",
            Purchase.paid_at >= day_start,
            Purchase.paid_at <= day_end
        ).count()
        
        revenue_chart.append({
            "date": date.isoformat(),
            "revenue_cents": day_revenue,
            "purchases": day_purchases
        })
    
    # Top datasets
    top_datasets = db.query(
        Dataset.name,
        Dataset.slug,
        Dataset.total_purchases,
        Dataset.total_revenue_cents
    ).order_by(Dataset.total_revenue_cents.desc()).limit(5).all()
    
    top_datasets_list = [
        {
            "name": d.name,
            "slug": d.slug,
            "purchases": d.total_purchases,
            "revenue_cents": d.total_revenue_cents
        }
        for d in top_datasets
    ]
    
    # Recent purchases
    recent_purchases = db.query(Purchase).options(
        joinedload(Purchase.user),
        joinedload(Purchase.dataset)
    ).filter(
        Purchase.status == "paid"
    ).order_by(Purchase.paid_at.desc()).limit(10).all()
    
    recent_list = [
        {
            "id": str(p.id),
            "user_email": p.user.email if p.user else "Unknown",
            "dataset_name": p.dataset.name if p.dataset else "Unknown",
            "amount_cents": p.amount_cents,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None
        }
        for p in recent_purchases
    ]
    
    return DashboardResponse(
        stats=DashboardStats(
            total_revenue_cents=total_revenue,
            total_purchases=total_purchases,
            total_users=total_users,
            total_datasets=total_datasets,
            revenue_this_month=revenue_this_month,
            purchases_this_month=purchases_this_month,
            signups_this_month=signups_this_month,
            revenue_change=revenue_change
        ),
        revenue_chart=revenue_chart,
        top_datasets=top_datasets_list,
        recent_purchases=recent_list
    )


# ============================================================
# Dataset Management
# ============================================================

@router.get("/datasets", response_model=List[DatasetAdminResponse])
async def list_all_datasets(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    List all datasets (including unpublished).
    """
    datasets = db.query(Dataset).options(
        joinedload(Dataset.category),
        joinedload(Dataset.fields)
    ).order_by(Dataset.created_at.desc()).all()
    
    result = []
    for d in datasets:
        result.append(DatasetAdminResponse(
            id=d.id,
            name=d.name,
            slug=d.slug,
            description=d.description,
            location=d.location,
            company_count=d.company_count,
            enrichment_level=d.enrichment_level,
            price_cents=d.price_cents,
            is_published=d.is_published,
            csv_file_path=d.csv_file_path,
            total_purchases=d.total_purchases,
            total_revenue_cents=d.total_revenue_cents,
            category=CategoryResponse(
                id=d.category.id,
                name=d.category.name,
                slug=d.category.slug,
                icon=d.category.icon
            ) if d.category else None,
            fields=[],
            sample_preview_json=d.sample_preview_json,
            last_updated_at=d.last_updated_at,
            created_at=d.created_at,
            updated_at=d.updated_at
        ))
    
    return result


@router.post("/datasets/upload-csv")
async def upload_csv_file(
    file: UploadFile = File(...),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Upload a CSV file, validate it, and store it in R2.
    Returns file metadata including company count and preview.
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed"
        )

    try:
        # Read file content
        content = await file.read()

        # Parse CSV to extract metadata
        csv_text = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_text))

        # Get headers and rows
        rows = list(csv_reader)
        if not rows:
            raise HTTPException(status_code=400, detail="CSV file is empty")

        headers = list(rows[0].keys())
        company_count = len(rows)

        # Detect enrichment level based on headers
        has_email = any('email' in h.lower() for h in headers)
        has_phone = any('phone' in h.lower() for h in headers)

        enrichment_level = 'email_and_phone' if (has_email and has_phone) else 'phone_only'

        # Create sample preview (first 5 rows)
        sample_preview = rows[:5]

        # Upload to R2 storage
        storage = StorageService()
        safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = await storage.upload_csv(content, safe_filename)

        # Log action
        await log_admin_action(
            db, str(admin.id), "upload_csv",
            "file", file_path,
            {"filename": file.filename, "company_count": company_count}
        )

        return {
            "success": True,
            "file_path": file_path,
            "filename": file.filename,
            "company_count": company_count,
            "enrichment_level": enrichment_level,
            "headers": headers,
            "sample_preview": sample_preview
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid CSV file encoding. Please use UTF-8."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process CSV: {str(e)}"
        )


@router.post("/datasets", response_model=DatasetAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    dataset_data: DatasetCreate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new dataset.
    """
    # Generate slug
    slug = generate_slug(dataset_data.name)

    # Ensure unique slug
    existing = db.query(Dataset).filter(Dataset.slug == slug).first()
    if existing:
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    dataset = Dataset(
        name=dataset_data.name,
        slug=slug,
        description=dataset_data.description,
        location=dataset_data.location,
        category_id=dataset_data.category_id,
        company_count=dataset_data.company_count,
        enrichment_level=dataset_data.enrichment_level,
        price_cents=dataset_data.price_cents,
        csv_file_path=dataset_data.csv_file_path,
        is_published=False,
        sample_preview_json=dataset_data.sample_preview_json
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    # Log action
    await log_admin_action(
        db, str(admin.id), "create_dataset",
        "dataset", str(dataset.id),
        {"name": dataset.name}
    )

    return DatasetAdminResponse(
        id=dataset.id,
        name=dataset.name,
        slug=dataset.slug,
        description=dataset.description,
        location=dataset.location,
        company_count=dataset.company_count,
        enrichment_level=dataset.enrichment_level,
        price_cents=dataset.price_cents,
        is_published=dataset.is_published,
        csv_file_path=dataset.csv_file_path,
        total_purchases=0,
        total_revenue_cents=0,
        category=None,
        fields=[],
        sample_preview_json=dataset.sample_preview_json,
        last_updated_at=None,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at
    )


@router.patch("/datasets/{dataset_id}", response_model=DatasetAdminResponse)
async def update_dataset(
    dataset_id: int,
    update_data: DatasetUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update a dataset.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(dataset, field, value)
    
    dataset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(dataset)
    
    # Log action
    await log_admin_action(
        db, str(admin.id), "update_dataset",
        "dataset", str(dataset.id),
        {"updated_fields": list(update_dict.keys())}
    )
    
    return DatasetAdminResponse(
        id=dataset.id,
        name=dataset.name,
        slug=dataset.slug,
        description=dataset.description,
        location=dataset.location,
        company_count=dataset.company_count,
        enrichment_level=dataset.enrichment_level,
        price_cents=dataset.price_cents,
        is_published=dataset.is_published,
        csv_file_path=dataset.csv_file_path,
        total_purchases=dataset.total_purchases,
        total_revenue_cents=dataset.total_revenue_cents,
        category=None,
        fields=[],
        sample_preview_json=dataset.sample_preview_json,
        last_updated_at=dataset.last_updated_at,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at
    )


@router.post("/datasets/{dataset_id}/publish")
async def publish_dataset(
    dataset_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Publish a dataset (make it available for purchase).
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    dataset.is_published = True
    dataset.updated_at = datetime.utcnow()
    db.commit()
    
    await log_admin_action(
        db, str(admin.id), "publish_dataset",
        "dataset", str(dataset.id)
    )
    
    return {"message": "Dataset published", "slug": dataset.slug}


@router.post("/datasets/{dataset_id}/unpublish")
async def unpublish_dataset(
    dataset_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Unpublish a dataset (hide from purchase).
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    dataset.is_published = False
    dataset.updated_at = datetime.utcnow()
    db.commit()
    
    await log_admin_action(
        db, str(admin.id), "unpublish_dataset",
        "dataset", str(dataset.id)
    )
    
    return {"message": "Dataset unpublished"}


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a dataset.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Check for existing purchases
    purchase_count = db.query(Purchase).filter(
        Purchase.dataset_id == dataset_id,
        Purchase.status == "paid"
    ).count()
    
    if purchase_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: {purchase_count} users have purchased this dataset"
        )
    
    await log_admin_action(
        db, str(admin.id), "delete_dataset",
        "dataset", str(dataset.id),
        {"name": dataset.name}
    )
    
    db.delete(dataset)
    db.commit()
    
    return {"message": "Dataset deleted"}


# ============================================================
# Purchase Management
# ============================================================

@router.get("/purchases", response_model=PaginatedPurchaseDetailResponse)
async def list_purchases(
    status_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    List all purchases.
    """
    query = db.query(Purchase).options(
        joinedload(Purchase.user),
        joinedload(Purchase.dataset)
    )
    
    if status_filter:
        query = query.filter(Purchase.status == status_filter)
    
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    
    purchases = query.order_by(Purchase.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    items = []
    for p in purchases:
        items.append(PurchaseDetailResponse(
            id=str(p.id),
            user_id=str(p.user_id),
            user_email=p.user.email if p.user else None,
            dataset=None,
            amount_cents=p.amount_cents,
            paystack_reference=p.paystack_reference,
            status=p.status,
            refund_amount_cents=p.refund_amount_cents,
            refund_reason=p.refund_reason,
            refunded_at=p.refunded_at,
            paid_at=p.paid_at,
            created_at=p.created_at
        ))
    
    return PaginatedPurchaseDetailResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/purchases/{purchase_id}/refund")
async def refund_purchase(
    purchase_id: str,
    refund_data: RefundRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Issue a refund for a purchase.
    """
    purchase = db.query(Purchase).options(
        joinedload(Purchase.user),
        joinedload(Purchase.dataset)
    ).filter(Purchase.id == purchase_id).first()
    
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    if purchase.status != "paid":
        raise HTTPException(status_code=400, detail="Can only refund paid purchases")
    
    if purchase.refunded_at:
        raise HTTPException(status_code=400, detail="Already refunded")
    
    # Process refund with Paystack
    payment_service = PaymentService()
    
    try:
        refund_result = await payment_service.refund_transaction(
            purchase.paystack_reference
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refund failed: {str(e)}")
    
    # Update purchase
    purchase.status = "refunded"
    purchase.refund_amount_cents = purchase.amount_cents
    purchase.refund_reason = refund_data.reason
    purchase.refunded_by = admin.id
    purchase.refunded_at = datetime.utcnow()
    db.commit()
    
    # Log action
    await log_admin_action(
        db, str(admin.id), "refund_purchase",
        "purchase", str(purchase.id),
        {"reason": refund_data.reason, "amount": purchase.amount_cents}
    )
    
    # Send email
    if purchase.user and purchase.dataset:
        email_service = EmailService()
        await email_service.send_refund_confirmation(
            email=purchase.user.email,
            name=purchase.user.name,
            dataset_name=purchase.dataset.name,
            amount_cents=purchase.amount_cents,
            reason=refund_data.reason
        )
    
    return {"message": "Refund processed", "refund_amount_cents": purchase.amount_cents}


# ============================================================
# User Management
# ============================================================

@router.get("/users", response_model=PaginatedUserResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    List all users.
    """
    query = db.query(User)
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    
    users = query.order_by(User.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    items = []
    for u in users:
        # Get purchase stats
        purchase_stats = db.query(
            func.count(Purchase.id).label("count"),
            func.sum(Purchase.amount_cents).label("total")
        ).filter(
            Purchase.user_id == u.id,
            Purchase.status == "paid"
        ).first()
        
        items.append(UserAdminResponse(
            id=str(u.id),
            email=u.email,
            name=u.name,
            is_active=u.is_active,
            email_verified=u.email_verified,
            created_at=u.created_at,
            last_login_at=u.last_login_at,
            total_purchases=purchase_stats.count or 0,
            total_spent_cents=purchase_stats.total or 0
        ))
    
    return PaginatedUserResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    status_data: UserStatusUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Activate or deactivate a user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = status_data.is_active
    user.updated_at = datetime.utcnow()
    db.commit()
    
    action = "activate_user" if status_data.is_active else "deactivate_user"
    await log_admin_action(
        db, str(admin.id), action,
        "user", str(user.id)
    )
    
    return {"message": f"User {'activated' if status_data.is_active else 'deactivated'}"}
