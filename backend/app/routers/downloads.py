from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.purchase import Purchase, DownloadLog, PurchaseStatus
from app.services.storage_service import StorageService

router = APIRouter()

@router.get("/{purchase_id}")
async def download_dataset(
    purchase_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate signed download URL for purchased dataset"""
    # Verify purchase
    purchase = db.query(Purchase).filter(
        Purchase.id == purchase_id,
        Purchase.user_id == current_user.id,
        Purchase.status == PurchaseStatus.PAID
    ).first()
    
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    if not purchase.dataset:
        raise HTTPException(status_code=404, detail="Dataset no longer available")
    
    # Generate signed URL
    storage = StorageService()
    download_url = await storage.generate_download_url(
        purchase.dataset.csv_file_path,
        expires_in=3600  # 1 hour
    )
    
    # Log download
    log = DownloadLog(
        purchase_id=purchase.id,
        user_id=current_user.id,
        dataset_id=purchase.dataset.id,
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent"),
        downloaded_at=datetime.utcnow()
    )
    db.add(log)
    db.commit()
    
    return {
        "download_url": download_url,
        "filename": f"{purchase.dataset.slug}.csv",
        "expires_in": 3600
    }