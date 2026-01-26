"""
Dataset model - Core product for the Helpuvio marketplace
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, BigInteger, ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Category(Base):
    """
    Category model - Maps to your existing categories table.
    Used for classifying datasets.
    """
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    icon = Column(String(50))
    description = Column(Text)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    
    # Relationships
    datasets = relationship("Dataset", back_populates="category")
    
    def __repr__(self):
        return f"<Category {self.name}>"


class Dataset(Base):
    """
    Dataset model - The core product for sale.
    
    Datasets contain:
    - 'phone_only': Companies with phone numbers only (cheaper)
    - 'email_and_phone': Companies with both email AND phone (premium)
    """
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True)
    
    # Basic info
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # Classification
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    location = Column(String(200))  # "Lagos, Nigeria", "Global"
    
    # Metadata
    company_count = Column(Integer, nullable=False, default=0)
    
    # CRITICAL: Determines pricing
    # 'phone_only' = Companies with phone only (cheaper)
    # 'email_and_phone' = Companies with email AND phone (premium)
    enrichment_level = Column(String(50), nullable=False, default='phone_only')
    
    # Pricing in cents (or kobo for NGN)
    price_cents = Column(Integer, nullable=False)
    
    # File storage
    csv_file_path = Column(String(500))  # S3/R2 URL
    
    # Sample preview (first 5 rows with redacted data)
    sample_preview_json = Column(JSONB)
    
    # Publishing
    is_published = Column(Boolean, default=False, index=True)
    
    # Stats
    total_purchases = Column(Integer, default=0)
    total_revenue_cents = Column(BigInteger, default=0)
    
    # Timestamps
    last_updated_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("NOW()"))
    
    # Relationships
    category = relationship("Category", back_populates="datasets")
    fields = relationship("DatasetField", back_populates="dataset", cascade="all, delete-orphan")
    purchases = relationship("Purchase", back_populates="dataset")
    companies = relationship("Company", back_populates="dataset")
    
    @property
    def price_display(self) -> str:
        """Format price for display (e.g., $29.99 or ₦2,999)"""
        return f"${self.price_cents / 100:.2f}"
    
    @property
    def is_premium(self) -> bool:
        """Check if this is a premium (email_and_phone) dataset"""
        return self.enrichment_level == "email_and_phone"
    
    def __repr__(self):
        return f"<Dataset {self.name}>"


class DatasetField(Base):
    """
    Fields included in a dataset.
    Used for the "What's Included" section on detail pages.
    """
    __tablename__ = "dataset_fields"
    
    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"))
    
    field_name = Column(String(100), nullable=False)  # "company_email"
    field_label = Column(String(100))  # "Company Email"
    is_enriched = Column(Boolean, default=False)  # Only in premium tier
    display_order = Column(Integer, default=0)
    
    # Relationships
    dataset = relationship("Dataset", back_populates="fields")
    
    def __repr__(self):
        return f"<DatasetField {self.field_name}>"