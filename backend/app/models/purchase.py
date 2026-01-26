from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Numeric, Enum as SQLEnum, text
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
import uuid

class PurchaseStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

class Purchase(Base):
    __tablename__ = "purchases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="SET NULL"))
    
    # Purchase details
    quantity = Column(Integer, nullable=True)  # Number of companies purchased
    
    # Payment
    amount_cents = Column(Integer, nullable=False)
    amount_usd = Column(Numeric(10, 2))
    amount_naira = Column(Numeric(12, 2))
    exchange_rate = Column(Numeric(10, 4))  # USD to Naira exchange rate at time of purchase
    
    paystack_reference = Column(String(200), unique=True, nullable=False, index=True)
    paystack_authorization_code = Column(String(200))
    
    # Status
    status = Column(SQLEnum(PurchaseStatus), default=PurchaseStatus.PENDING, index=True)
    
    # Refunds
    refund_amount_cents = Column(Integer)
    refund_reason = Column(Text)
    refunded_by = Column(UUID(as_uuid=True))
    refunded_at = Column(TIMESTAMP(timezone=True))
    
    # Timestamps
    paid_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('NOW()'))
    
    # Relationships
    user = relationship("User", back_populates="purchases")
    dataset = relationship("Dataset", back_populates="purchases")
    download_logs = relationship("DownloadLog", back_populates="purchase")

class DownloadLog(Base):
    __tablename__ = "download_logs"
    
    id = Column(Integer, primary_key=True)
    purchase_id = Column(UUID(as_uuid=True), ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="SET NULL"))
    
    # Request metadata
    ip_address = Column(INET, nullable=False)
    user_agent = Column(Text)
    country_code = Column(String(5))
    
    # Timestamp
    downloaded_at = Column(TIMESTAMP(timezone=True), server_default=text('NOW()'))
    
    # Relationships
    purchase = relationship("Purchase", back_populates="download_logs")
    user = relationship("User", back_populates="download_logs")

