# app/routers/datasets.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import List, Optional
from app.core.database import get_db
from app.models.dataset import Dataset, Category, DatasetField
from app.schemas.dataset import (
    DatasetResponse, 
    DatasetDetail, 
    DatasetListResponse,
    CategoryResponse,
    CategorySimple
)

# REMOVE prefix="/datasets" from here
router = APIRouter(tags=["datasets"])

# Rest of your code stays the same...
@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    category: Optional[str] = None,
    location: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # ... rest of your code
    """
    Get all published datasets with optional filters
    
    Parameters:
    - category: Filter by category slug
    - location: Filter by location (case-insensitive partial match)
    - min_price: Minimum price in dollars
    - max_price: Maximum price in dollars
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    """
    # Base query - only published datasets
    query = db.query(Dataset).options(
        joinedload(Dataset.category)
    ).filter(Dataset.is_published == True)
    
    # Apply filters
    if category:
        query = query.join(Category).filter(Category.slug == category)
    
    if location:
        query = query.filter(Dataset.location.ilike(f"%{location}%"))
    
    if min_price is not None:
        query = query.filter(Dataset.price_cents >= min_price * 100)
    
    if max_price is not None:
        query = query.filter(Dataset.price_cents <= max_price * 100)
    
    # Order by newest first
    query = query.order_by(Dataset.created_at.desc())
    
    # Get datasets
    datasets = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Convert to response format
    return [
        DatasetResponse(
            id=d.id,
            name=d.name,
            slug=d.slug,
            description=d.description,
            category=CategorySimple(
                id=d.category.id,
                name=d.category.name,
                slug=d.category.slug,
                icon=d.category.icon
            ) if d.category else None,
            location=d.location,
            company_count=d.company_count,
            price=d.price_cents / 100,  # Convert cents to dollars
            enrichment_level=d.enrichment_level,
            is_published=d.is_published,
            total_purchases=d.total_purchases or 0,
            created_at=d.created_at
        )
        for d in datasets
    ]

@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(db: Session = Depends(get_db)):
    """Get all active categories"""
    categories = db.query(Category).filter(
        Category.is_active == True
    ).order_by(Category.display_order).all()
    
    return categories

@router.get("/{slug}", response_model=DatasetDetail)
async def get_dataset(slug: str, db: Session = Depends(get_db)):
    """
    Get dataset details by slug
    
    Returns:
    - Full dataset information
    - Sample preview (redacted emails/phones)
    - List of included fields
    """
    dataset = db.query(Dataset).options(
        joinedload(Dataset.category),
        joinedload(Dataset.fields)
    ).filter(
        Dataset.slug == slug,
        Dataset.is_published == True
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return DatasetDetail(
        id=dataset.id,
        name=dataset.name,
        slug=dataset.slug,
        description=dataset.description,
        category=CategorySimple(
            id=dataset.category.id,
            name=dataset.category.name,
            slug=dataset.category.slug,
            icon=dataset.category.icon
        ) if dataset.category else None,
        location=dataset.location,
        company_count=dataset.company_count,
        price=dataset.price_cents / 100,
        enrichment_level=dataset.enrichment_level,
        sample_preview=dataset.sample_preview_json,
        fields=[
            {
                "field_name": f.field_name,
                "field_label": f.field_label,
                "is_enriched": f.is_enriched,
                "display_order": f.display_order
            }
            for f in sorted(dataset.fields, key=lambda x: x.display_order)
        ] if dataset.fields else [],
        total_purchases=dataset.total_purchases or 0,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at
    )

@router.get("/stats/summary")
async def get_dataset_stats(db: Session = Depends(get_db)):
    """Get dataset statistics"""
    total_datasets = db.query(func.count(Dataset.id)).filter(
        Dataset.is_published == True
    ).scalar()
    
    total_companies = db.query(func.sum(Dataset.company_count)).filter(
        Dataset.is_published == True
    ).scalar() or 0
    
    total_purchases = db.query(func.sum(Dataset.total_purchases)).filter(
        Dataset.is_published == True
    ).scalar() or 0
    
    return {
        "total_datasets": total_datasets,
        "total_companies": total_companies,
        "total_purchases": total_purchases
    }