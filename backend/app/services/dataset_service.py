from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.dataset import Dataset, Category

class DatasetService:
    @staticmethod
    def get_published_datasets(
        db: Session,
        category: Optional[str] = None,
        location: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
    ) -> List[Dataset]:
        """Get all published datasets with filters"""
        query = db.query(Dataset).filter(Dataset.is_published == True)
        
        if category:
            query = query.join(Category).filter(Category.slug == category)
        
        if location:
            query = query.filter(Dataset.location.ilike(f"%{location}%"))
        
        if min_price:
            query = query.filter(Dataset.price_cents >= min_price * 100)
        
        if max_price:
            query = query.filter(Dataset.price_cents <= max_price * 100)
        
        return query.order_by(Dataset.created_at.desc()).all()
    
    @staticmethod
    def get_dataset_by_slug(db: Session, slug: str) -> Dataset | None:
        """Get dataset by slug"""
        return db.query(Dataset).filter(
            Dataset.slug == slug,
            Dataset.is_published == True
        ).first()