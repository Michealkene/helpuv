"""
Datasets Router - Browse and view dataset details
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List
import re

from app.core.database import get_db
from app.core.dependencies import get_current_user_optional
from app.models.dataset import Dataset, Category, DatasetField
from app.models.purchase import Purchase
from app.models.user import User
from app.schemas.dataset import (
    DatasetListResponse,
    DatasetDetailResponse,
    CategoryResponse,
    DatasetFieldResponse,
    PaginatedDatasetResponse
)

router = APIRouter(tags=["datasets"])


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a name"""
    slug = name.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug.strip('-')


@router.get("", response_model=PaginatedDatasetResponse)
async def list_datasets(
    category: Optional[str] = Query(None, description="Filter by category slug"),
    state: Optional[str] = Query(None, description="Filter by US state"),
    city: Optional[str] = Query(None, description="Filter by city"),
    min_price: Optional[int] = Query(None, ge=0, description="Minimum price in cents"),
    max_price: Optional[int] = Query(None, ge=0, description="Maximum price in cents"),
    enrichment_level: Optional[str] = Query(None, description="phone_only or email_and_phone"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Browse published datasets with filters.

    Filters:
    - category: Category slug (e.g., "technology")
    - state: US state code (e.g., "FL", "CA")
    - city: City name (exact match)
    - min_price/max_price: Price range in cents
    - enrichment_level: "phone_only" (cheaper) or "email_and_phone" (premium)
    """
    # Base query - only published datasets
    query = db.query(Dataset).filter(Dataset.is_published == True)

    # Apply filters
    if category:
        query = query.join(Category).filter(Category.slug == category)

    if state:
        query = query.filter(Dataset.location.ilike(f"%{state}%"))

    if city:
        query = query.filter(Dataset.location.ilike(f"%{city}%"))
    
    if min_price is not None:
        query = query.filter(Dataset.price_cents >= min_price)
    
    if max_price is not None:
        query = query.filter(Dataset.price_cents <= max_price)
    
    if enrichment_level:
        query = query.filter(Dataset.enrichment_level == enrichment_level)
    
    # Get total count
    total = query.count()
    
    # Calculate pagination
    total_pages = (total + page_size - 1) // page_size
    offset = (page - 1) * page_size
    
    # Get paginated results with category eagerly loaded
    datasets = query.options(
        joinedload(Dataset.category)
    ).order_by(
        Dataset.total_purchases.desc(),
        Dataset.created_at.desc()
    ).offset(offset).limit(page_size).all()
    
    # Convert to response
    items = []
    for dataset in datasets:
        items.append(DatasetListResponse(
            id=dataset.id,
            name=dataset.name,
            slug=dataset.slug,
            description=dataset.description,
            location=dataset.location,
            company_count=dataset.company_count,
            enrichment_level=dataset.enrichment_level,
            price_cents=dataset.price_cents,
            category=CategoryResponse(
                id=dataset.category.id,
                name=dataset.category.name,
                slug=dataset.category.slug,
                icon=dataset.category.icon,
                description=dataset.category.description
            ) if dataset.category else None,
            total_purchases=dataset.total_purchases
        ))
    
    return PaginatedDatasetResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    db: Session = Depends(get_db)
):
    """
    Get all active categories that have at least one dataset.
    """
    # Only return categories that have datasets
    categories = db.query(Category).filter(
        Category.is_active == True
    ).join(Dataset, Category.id == Dataset.category_id).distinct().order_by(
        Category.display_order, Category.name
    ).all()

    return [
        CategoryResponse(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            icon=cat.icon,
            description=cat.description
        )
        for cat in categories
    ]


@router.get("/cities", response_model=List[str])
async def list_cities(
    state: str = Query(..., description="US state code"),
    db: Session = Depends(get_db)
):
    """
    Get all cities for a given US state from the companies table.
    """
    from app.models.company import Company
    import re

    # Query distinct cities for the given state
    cities_raw = db.query(Company.city).filter(
        Company.state == state,
        Company.city.isnot(None),
        Company.city != ''
    ).distinct().all()

    # Clean city names - extract just the city part without zip codes
    cities_clean = set()
    for city_tuple in cities_raw:
        city = city_tuple[0]
        if city:
            # Remove zip codes and extra formatting
            # Pattern: "City Name, ST 12345" -> "City Name"
            city_cleaned = re.sub(r',\s*(FL|[A-Z]{2})\s*\d+.*$', '', city).strip()
            if city_cleaned:
                cities_clean.add(city_cleaned)

    return sorted(list(cities_clean))


@router.get("/{slug}", response_model=DatasetDetailResponse)
async def get_dataset_detail(
    slug: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get dataset detail by slug.
    
    Includes:
    - Full description
    - Category info
    - Fields included (what's in the dataset)
    - Sample preview (redacted data)
    - Pricing
    """
    # Find dataset
    dataset = db.query(Dataset).options(
        joinedload(Dataset.category),
        joinedload(Dataset.fields)
    ).filter(
        Dataset.slug == slug,
        Dataset.is_published == True
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Convert fields
    fields = [
        DatasetFieldResponse(
            id=field.id,
            field_name=field.field_name,
            field_label=field.field_label,
            is_enriched=field.is_enriched,
            display_order=field.display_order
        )
        for field in sorted(dataset.fields, key=lambda x: x.display_order)
    ]
    
    return DatasetDetailResponse(
        id=dataset.id,
        name=dataset.name,
        slug=dataset.slug,
        description=dataset.description,
        location=dataset.location,
        company_count=dataset.company_count,
        enrichment_level=dataset.enrichment_level,
        price_cents=dataset.price_cents,
        category=CategoryResponse(
            id=dataset.category.id,
            name=dataset.category.name,
            slug=dataset.category.slug,
            icon=dataset.category.icon,
            description=dataset.category.description
        ) if dataset.category else None,
        fields=fields,
        sample_preview_json=dataset.sample_preview_json,
        total_purchases=dataset.total_purchases,
        last_updated_at=dataset.last_updated_at,
        created_at=dataset.created_at
    )


@router.get("/{slug}/check-purchase")
async def check_purchase_status(
    slug: str,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Check if current user has purchased this dataset.
    Useful for showing "Download" vs "Purchase" button.
    """
    if not current_user:
        return {"purchased": False, "purchase_id": None}
    
    # Find dataset
    dataset = db.query(Dataset).filter(Dataset.slug == slug).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Check purchase
    purchase = db.query(Purchase).filter(
        Purchase.user_id == current_user.id,
        Purchase.dataset_id == dataset.id,
        Purchase.status == "paid"
    ).first()
    
    return {
        "purchased": purchase is not None,
        "purchase_id": str(purchase.id) if purchase else None
    }