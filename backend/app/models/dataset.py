from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, BigInteger, ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    icon = Column(String(50))
    description = Column(Text)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('NOW()'))
    
    # Relationships
    datasets = relationship("Dataset", back_populates="category")

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # Classification
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    location = Column(String(200))
    
    # Metadata
    company_count = Column(Integer, nullable=False)
    enrichment_level = Column(String(50), nullable=False)
    
    # Pricing
    price_cents = Column(Integer, nullable=False)
    
    # File storage
    csv_file_path = Column(String(500), nullable=False)
    sample_preview_json = Column(JSONB)
    
    # Publishing
    is_published = Column(Boolean, default=False, index=True)
    
    # Stats
    total_purchases = Column(Integer, default=0)
    total_revenue_cents = Column(BigInteger, default=0)
    
    # Timestamps
    last_updated_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('NOW()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('NOW()'), onupdate=text('NOW()'))
    
    # Relationships
    category = relationship("Category", back_populates="datasets")
    fields = relationship("DatasetField", back_populates="dataset", cascade="all, delete-orphan")
    purchases = relationship("Purchase", back_populates="dataset")

class DatasetField(Base):
    __tablename__ = "dataset_fields"
    
    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String(100), nullable=False)
    field_label = Column(String(100))
    is_enriched = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    
    # Relationships
    dataset = relationship("Dataset", back_populates="fields")