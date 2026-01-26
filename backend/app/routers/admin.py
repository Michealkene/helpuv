from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import List
import csv
import io
import json
from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.models.admin import AdminUser, AdminAuditLog
from app.models.user import User
from app.models.dataset import Dataset, Category, DatasetField
from app.models.purchase import Purchase, PurchaseStatus
from app.schemas.admin import AdminLogin, AdminTokenResponse, DashboardStatsResponse
from app.schemas.dataset import DatasetCreate, DatasetUpdate
from app.schemas.purchase import RefundRequest
from app.services.storage_service import StorageService

router = APIRouter()

# Admin Authentication
@router.post("/login", response_model=AdminTokenResponse)
async def admin_login(data: AdminLogin, db: Session = Depends(get_db)):
    """Admin login"""
    admin = db.query(AdminUser).filter(AdminUser.email == data.email).first()
    
    if not admin or not verify_password(data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is disabled"
        )
    
    # Update last login
    admin.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token({
        "sub": str(admin.id),
        "email": admin.email,
        "role": "admin"
    })
    refresh_token = create_refresh_token({"sub": str(admin.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "admin": admin
    }

# Dashboard Stats
@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    now = datetime.utcnow()
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Total counts
    total_users = db.query(func.count(User.id)).scalar()
    total_datasets = db.query(func.count(Dataset.id)).filter(Dataset.is_published == True).scalar()
    total_purchases = db.query(func.count(Purchase.id)).filter(Purchase.status == PurchaseStatus.PAID).scalar()
    
    # Total revenue
    total_revenue_cents = db.query(func.sum(Purchase.amount_cents)).filter(
        Purchase.status == PurchaseStatus.PAID
    ).scalar() or 0
    
    # This month stats
    revenue_this_month_cents = db.query(func.sum(Purchase.amount_cents)).filter(
        Purchase.status == PurchaseStatus.PAID,
        Purchase.paid_at >= first_day_of_month
    ).scalar() or 0
    
    purchases_this_month = db.query(func.count(Purchase.id)).filter(
        Purchase.status == PurchaseStatus.PAID,
        Purchase.paid_at >= first_day_of_month
    ).scalar()
    
    signups_this_month = db.query(func.count(User.id)).filter(
        User.created_at >= first_day_of_month
    ).scalar()
    
    return {
        "total_users": total_users,
        "total_datasets": total_datasets,
        "total_purchases": total_purchases,
        "total_revenue": total_revenue_cents / 100,
        "revenue_this_month": revenue_this_month_cents / 100,
        "purchases_this_month": purchases_this_month,
        "signups_this_month": signups_this_month
    }

# Datasets Management
@router.get("/datasets")
async def list_admin_datasets(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all datasets (including unpublished)"""
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    
    return [
        {
            "id": d.id,
            "name": d.name,
            "slug": d.slug,
            "company_count": d.company_count,
            "price": d.price_cents / 100,
            "is_published": d.is_published,
            "total_purchases": d.total_purchases,
            "total_revenue": d.total_revenue_cents / 100,
            "created_at": d.created_at
        }
        for d in datasets
    ]

@router.post("/datasets")
async def create_dataset(
    name: str,
    slug: str,
    description: str,
    category_id: int,
    location: str,
    company_count: int,
    enrichment_level: str,
    price_cents: int,
    file: UploadFile = File(...),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Upload new dataset"""
    # Validate file
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
    
    # Upload to storage
    storage = StorageService()
    file_path = await storage.upload_dataset_csv(file, 0)
    
    # Parse sample preview (first 5 rows)
    file.file.seek(0)
    content = await file.read()
    csv_reader = csv.DictReader(io.StringIO(content.decode('utf-8')))
    sample_rows = []
    
    for i, row in enumerate(csv_reader):
        if i >= 5:
            break
        # Redact sensitive fields
        redacted_row = {}
        for key, value in row.items():
            if 'email' in key.lower():
                redacted_row[key] = value[:2] + "***@" + value.split('@')[1] if '@' in value else "***"
            elif 'phone' in key.lower():
                redacted_row[key] = value[:4] + "***" + value[-4:] if len(value) > 8 else "***"
            else:
                redacted_row[key] = value
        sample_rows.append(redacted_row)
    
    # Create dataset
    dataset = Dataset(
        name=name,
        slug=slug,
        description=description,
        category_id=category_id,
        location=location,
        company_count=company_count,
        enrichment_level=enrichment_level,
        price_cents=price_cents,
        csv_file_path=file_path,
        sample_preview_json=sample_rows,
        is_published=False
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    # Log action
    log = AdminAuditLog(
        admin_id=admin.id,
        action="create_dataset",
        resource_type="dataset",
        resource_id=str(dataset.id),
        details={"name": name, "slug": slug}
    )
    db.add(log)
    db.commit()
    
    return {"id": dataset.id, "message": "Dataset created successfully"}

@router.patch("/datasets/{dataset_id}")
async def update_dataset(
    dataset_id: int,
    data: DatasetUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update dataset"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Update fields
    for key, value in data.dict(exclude_unset=True).items():
        setattr(dataset, key, value)
    
    db.commit()
    
    # Log action
    log = AdminAuditLog(
        admin_id=admin.id,
        action="update_dataset",
        resource_type="dataset",
        resource_id=str(dataset_id),
        details=data.dict(exclude_unset=True)
    )
    db.add(log)
    db.commit()
    
    return {"message": "Dataset updated successfully"}

@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete dataset"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    db.delete(dataset)
    db.commit()
    
    # Log action
    log = AdminAuditLog(
        admin_id=admin.id,
        action="delete_dataset",
        resource_type="dataset",
        resource_id=str(dataset_id),
        details={"name": dataset.name}
    )
    db.add(log)
    db.commit()
    
    return {"message": "Dataset deleted successfully"}

# Purchases Management
@router.get("/purchases")
async def list_purchases(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all purchases"""
    purchases = db.query(Purchase).order_by(Purchase.created_at.desc()).limit(100).all()
    
    return [
        {
            "id": str(p.id),
            "user": {"email": p.user.email, "name": p.user.name} if p.user else None,
            "dataset": {"name": p.dataset.name} if p.dataset else None,
            "amount": p.amount_cents / 100,
            "status": p.status,
            "created_at": p.created_at,
            "paid_at": p.paid_at
        }
        for p in purchases
    ]

@router.post("/purchases/{purchase_id}/refund")
async def refund_purchase(
    purchase_id: str,
    data: RefundRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Issue refund"""
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    if purchase.status != PurchaseStatus.PAID:
        raise HTTPException(status_code=400, detail="Purchase not paid")
    
    if purchase.refunded_at:
        raise HTTPException(status_code=400, detail="Already refunded")
    
    # Update purchase
    purchase.status = PurchaseStatus.REFUNDED
    purchase.refund_amount_cents = purchase.amount_cents
    purchase.refund_reason = data.reason
    purchase.refunded_by = admin.id
    purchase.refunded_at = datetime.utcnow()
    db.commit()
    
    # Log action
    log = AdminAuditLog(
        admin_id=admin.id,
        action="refund_purchase",
        resource_type="purchase",
        resource_id=purchase_id,
        details={"reason": data.reason, "amount": purchase.amount_cents / 100}
    )
    db.add(log)
    db.commit()
    
    return {"message": "Refund issued successfully"}

# Users Management
@router.get("/users")
async def list_users(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """List all users"""
    users = db.query(User).order_by(User.created_at.desc()).limit(100).all()
    
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "is_active": u.is_active,
            "email_verified": u.email_verified,
            "created_at": u.created_at,
            "total_purchases": len([p for p in u.purchases if p.status == PurchaseStatus.PAID])
        }
        for u in users
    ]