from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, BigInteger, ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("category_groups.id"), nullable=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True, index=True)
    icon = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    
    # Relationships
    datasets = relationship("Dataset", back_populates="category")
    group = relationship("CategoryGroup", back_populates="categories")

class CategoryGroup(Base):
    __tablename__ = "category_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    slug = Column(String, nullable=False, unique=True, index=True)
    icon = Column(String, nullable=True)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    
    # Relationships
    categories = relationship("Category", back_populates="group")

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Classification
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    location = Column(String(200), nullable=True)
    
    # Metadata
    company_count = Column(Integer, nullable=False)
    enrichment_level = Column(String(50), nullable=False)  # 'company_only' or 'company_contacts'
    
    # Pricing
    price_cents = Column(Integer, nullable=False, index=True)
    
    # File storage
    csv_file_path = Column(String(500), nullable=False)
    sample_preview_json = Column(JSONB, nullable=True)
    
    # Publishing
    is_published = Column(Boolean, default=False, index=True)
    
    # Stats
    total_purchases = Column(Integer, default=0)
    total_revenue_cents = Column(BigInteger, default=0)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    
    # Relationships
    category = relationship("Category", back_populates="datasets")
    fields = relationship("DatasetField", back_populates="dataset", cascade="all, delete-orphan")
    purchases = relationship("Purchase", back_populates="dataset")

class DatasetField(Base):
    __tablename__ = "dataset_fields"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    field_label = Column(String(100), nullable=True)
    is_enriched = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    
    # Relationships
    dataset = relationship("Dataset", back_populates="fields")
    
    __table_args__ = (
        # Unique constraint on dataset_id + field_name
        # UniqueConstraint('dataset_id', 'field_name', name='uix_dataset_field'),
    )