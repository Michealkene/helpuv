"""
Downloads Router - Generate download URLs for purchased datasets
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
import logging
import csv
import io

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.purchase import Purchase, DownloadLog
from app.schemas.purchase import DownloadResponse
from app.services.storage_service import StorageService

router = APIRouter(prefix="/downloads", tags=["downloads"])
logger = logging.getLogger(__name__)

# Allowed columns in downloaded CSV (security measure)
ALLOWED_COLUMNS = ['categories', 'state', 'company', 'phone', 'email']


@router.get("/{purchase_id}")
async def download_dataset(
    purchase_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download purchased dataset with filtered columns.
    
    Security:
    - Verifies user owns the purchase
    - Purchase must be in "paid" status
    - Only returns specific columns: categories, state, company, phone, email
    - Logs download for audit trail
    """
    # 1. Verify purchase ownership and status
    purchase = db.query(Purchase).options(
        joinedload(Purchase.dataset)
    ).filter(
        Purchase.id == purchase_id,
        Purchase.user_id == current_user.id
    ).first()
    
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase not found"
        )
    
    if purchase.status != "paid":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Purchase not completed"
        )
    
    if purchase.status == "refunded":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This purchase has been refunded"
        )
    
    # 2. Check dataset still exists
    dataset = purchase.dataset
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset no longer available"
        )
    
    if not dataset.csv_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file not found"
        )
    
    # 3. Download and filter CSV
    storage = StorageService()
    
    if not storage.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Download service not available"
        )
    
    try:
        # Download CSV from storage
        csv_content = await storage.download_file(dataset.csv_file_path)
        
        # Parse and filter CSV
        input_csv = csv_content.decode('utf-8')
        input_file = io.StringIO(input_csv)
        reader = csv.DictReader(input_file)
        
        # Create filtered CSV with only allowed columns
        output = io.StringIO()
        
        # Get fieldnames and filter to only allowed columns
        if reader.fieldnames:
            # Only include columns that exist in both the CSV and allowed list
            filtered_fieldnames = [col for col in ALLOWED_COLUMNS if col in reader.fieldnames]
            
            if not filtered_fieldnames:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No valid columns found in dataset"
                )
            
            writer = csv.DictWriter(output, fieldnames=filtered_fieldnames)
            writer.writeheader()
            
            # Write filtered rows
            for row in reader:
                filtered_row = {col: row.get(col, '') for col in filtered_fieldnames}
                writer.writerow(filtered_row)
        
        # Get filtered CSV content
        filtered_csv = output.getvalue()
        
    except Exception as e:
        logger.error(f"Failed to process CSV: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process dataset: {str(e)}"
        )
    
    # 4. Log download for audit
    download_log = DownloadLog(
        purchase_id=purchase.id,
        user_id=current_user.id,
        dataset_id=dataset.id,
        ip_address=request.client.host if request.client else "0.0.0.0",
        user_agent=request.headers.get("User-Agent"),
        downloaded_at=datetime.utcnow()
    )
    
    db.add(download_log)
    db.commit()
    
    logger.info(f"Download generated: user={current_user.email}, dataset={dataset.slug}, size={len(filtered_csv)} bytes")
    
    # 5. Return filtered CSV as streaming response
    filename = f"{dataset.slug}.csv"
    
    return StreamingResponse(
        iter([filtered_csv]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/csv; charset=utf-8"
        }
    )


@router.get("/{purchase_id}/info")
async def get_download_info(
    purchase_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get download information without generating a new URL.
    
    Useful for showing download history and metadata.
    """
    purchase = db.query(Purchase).options(
        joinedload(Purchase.dataset),
        joinedload(Purchase.download_logs)
    ).filter(
        Purchase.id == purchase_id,
        Purchase.user_id == current_user.id,
        Purchase.status == "paid"
    ).first()
    
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase not found"
        )
    
    dataset = purchase.dataset
    
    return {
        "purchase_id": str(purchase.id),
        "dataset_name": dataset.name if dataset else "Unknown",
        "dataset_slug": dataset.slug if dataset else None,
        "company_count": dataset.company_count if dataset else 0,
        "enrichment_level": dataset.enrichment_level if dataset else None,
        "purchased_at": purchase.paid_at.isoformat() if purchase.paid_at else None,
        "download_count": len(purchase.download_logs),
        "last_downloaded_at": max(
            (log.downloaded_at for log in purchase.download_logs),
            default=None
        )
    }
