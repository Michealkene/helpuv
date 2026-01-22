from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from app.core.database import get_db
from app.models.dataset import Dataset, Category, DatasetField
from app.schemas.dataset import DatasetResponse, DatasetDetail, DatasetListResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=DatasetListResponse)
async def list_datasets(
    category: Optional[str] = Query(None, description="Filter by category slug"),
    location: Optional[str] = Query(None, description="Filter by location"),
    min_price: Optional[int] = Query(None, description="Minimum price in cents"),
    max_price: Optional[int] = Query(None, description="Maximum price in cents"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all published datasets with optional filters
    """
    try:
        # Base query - only published datasets
        query = db.query(Dataset).filter(Dataset.is_published == True)
        
        # Apply filters
        if category:
            query = query.join(Category).filter(Category.slug == category)
        
        if location:
            query = query.filter(Dataset.location.ilike(f"%{location}%"))
        
        if min_price is not None:
            query = query.filter(Dataset.price_cents >= min_price)
        
        if max_price is not None:
            query = query.filter(Dataset.price_cents <= max_price)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Dataset.name.ilike(search_term),
                    Dataset.description.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        datasets = query.order_by(Dataset.created_at.desc()).offset(offset).limit(limit).all()
        
        # Convert to response format
        dataset_list = []
        for dataset in datasets:
            category_info = None
            if dataset.category:
                category_info = {
                    "id": dataset.category.id,
                    "name": dataset.category.name,
                    "slug": dataset.category.slug,
                    "icon": dataset.category.icon
                }
            
            dataset_list.append({
                "id": dataset.id,
                "name": dataset.name,
                "slug": dataset.slug,
                "description": dataset.description,
                "category": category_info,
                "location": dataset.location,
                "company_count": dataset.company_count,
                "enrichment_level": dataset.enrichment_level,
                "price": dataset.price_cents / 100,  # Convert to dollars
                "price_cents": dataset.price_cents,
                "total_purchases": dataset.total_purchases,
                "created_at": dataset.created_at.isoformat()
            })
        
        return {
            "datasets": dataset_list,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    
    except Exception as e:
        logger.error(f"Error listing datasets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch datasets: {str(e)}")


@router.get("/categories")
async def list_categories(db: Session = Depends(get_db)):
    """
    List all active categories
    """
    try:
        categories = db.query(Category).filter(
            Category.is_active == True
        ).order_by(Category.display_order).all()
        
        return {
            "categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "slug": cat.slug,
                    "icon": cat.icon,
                    "description": cat.description
                }
                for cat in categories
            ]
        }
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch categories")


@router.get("/{slug}", response_model=DatasetDetail)
async def get_dataset_detail(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific dataset
    """
    try:
        dataset = db.query(Dataset).filter(
            and_(
                Dataset.slug == slug,
                Dataset.is_published == True
            )
        ).first()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Get dataset fields
        fields = db.query(DatasetField).filter(
            DatasetField.dataset_id == dataset.id
        ).order_by(DatasetField.display_order).all()
        
        # Category info
        category_info = None
        if dataset.category:
            category_info = {
                "id": dataset.category.id,
                "name": dataset.category.name,
                "slug": dataset.category.slug,
                "icon": dataset.category.icon
            }
        
        # Build field list
        field_list = [
            {
                "name": field.field_name,
                "label": field.field_label,
                "is_enriched": field.is_enriched
            }
            for field in fields
        ]
        
        return {
            "id": dataset.id,
            "name": dataset.name,
            "slug": dataset.slug,
            "description": dataset.description,
            "category": category_info,
            "location": dataset.location,
            "company_count": dataset.company_count,
            "enrichment_level": dataset.enrichment_level,
            "price": dataset.price_cents / 100,
            "price_cents": dataset.price_cents,
            "total_purchases": dataset.total_purchases,
            "fields": field_list,
            "sample_preview": dataset.sample_preview_json,
            "created_at": dataset.created_at.isoformat(),
            "last_updated": dataset.updated_at.isoformat() if dataset.updated_at else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dataset {slug}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch dataset: {str(e)}")