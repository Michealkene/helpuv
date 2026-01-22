from sqlalchemy.orm import Session
from app.models.purchase import Purchase, PurchaseStatus
from app.models.dataset import Dataset
import uuid

class PurchaseService:
    @staticmethod
    def create_purchase(
        db: Session,
        user_id: str,
        dataset_id: int
    ) -> Purchase:
        """Create new purchase"""
        # Check if already purchased
        existing = db.query(Purchase).filter(
            Purchase.user_id == user_id,
            Purchase.dataset_id == dataset_id,
            Purchase.status == PurchaseStatus.PAID
        ).first()
        
        if existing:
            return existing
        
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError("Dataset not found")
        
        # Create purchase
        purchase = Purchase(
            user_id=user_id,
            dataset_id=dataset_id,
            amount_cents=dataset.price_cents,
            paystack_reference=f"PUR-{uuid.uuid4().hex[:12].upper()}",
            status=PurchaseStatus.PENDING
        )
        
        db.add(purchase)
        db.commit()
        db.refresh(purchase)
        
        return purchase