# backend/app/workers/email_verification_worker.py
"""
Background worker for automated email verification

Run this as a separate process:
  python -m app.workers.email_verification_worker
"""

import time
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.email_verifier import EmailVerificationService
from app.models.email import Email

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailVerificationWorker:
    """Background worker for continuous email verification"""
    
    def __init__(self, batch_size: int = 50, sleep_interval: int = 60):
        """
        Initialize worker
        
        Args:
            batch_size: Number of emails to verify per batch
            sleep_interval: Seconds to sleep between batches
        """
        self.batch_size = batch_size
        self.sleep_interval = sleep_interval
        self.is_running = False
    
    def run(self):
        """Start the worker"""
        self.is_running = True
        logger.info(f"🚀 Email Verification Worker started")
        logger.info(f"   Batch size: {self.batch_size}")
        logger.info(f"   Sleep interval: {self.sleep_interval}s")
        
        while self.is_running:
            try:
                self.process_batch()
                logger.info(f"💤 Sleeping for {self.sleep_interval} seconds...")
                time.sleep(self.sleep_interval)
            except KeyboardInterrupt:
                logger.info("⛔ Received shutdown signal")
                self.stop()
            except Exception as e:
                logger.error(f"❌ Error in worker: {e}", exc_info=True)
                time.sleep(self.sleep_interval)
    
    def process_batch(self):
        """Process a batch of unverified emails"""
        db = SessionLocal()
        
        try:
            service = EmailVerificationService(db)
            
            # Get count of unverified emails
            unverified_count = db.query(Email).filter(
                Email.verified == False,
                Email.verification_status.is_(None)
            ).count()
            
            if unverified_count == 0:
                logger.info("✅ No unverified emails found")
                return
            
            logger.info(f"📧 Found {unverified_count} unverified emails")
            logger.info(f"🔍 Processing batch of {self.batch_size} emails...")
            
            # Verify batch
            result = service.verify_unverified_emails(limit=self.batch_size)
            
            logger.info(f"✅ Batch complete:")
            logger.info(f"   Total: {result['total']}")
            logger.info(f"   Valid: {result['verified']}")
            logger.info(f"   Invalid: {result['invalid']}")
            logger.info(f"   Risky: {result['risky']}")
            logger.info(f"   Unknown: {result['unknown']}")
            
        except Exception as e:
            logger.error(f"❌ Error processing batch: {e}", exc_info=True)
        finally:
            db.close()
    
    def stop(self):
        """Stop the worker"""
        self.is_running = False
        logger.info("🛑 Worker stopped")


class ScheduledVerificationWorker(EmailVerificationWorker):
    """Worker that runs verification on a schedule"""
    
    def __init__(self, batch_size: int = 50):
        super().__init__(batch_size=batch_size, sleep_interval=300)  # 5 minutes
        self.daily_verification_hour = 2  # Run full verification at 2 AM
    
    def run(self):
        """Run with scheduled tasks"""
        self.is_running = True
        logger.info(f"🚀 Scheduled Email Verification Worker started")
        logger.info(f"   Daily full verification at {self.daily_verification_hour}:00")
        
        last_daily_run = None
        
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check if it's time for daily full verification
                if (current_time.hour == self.daily_verification_hour and 
                    (last_daily_run is None or 
                     (current_time - last_daily_run).days >= 1)):
                    
                    logger.info("🌙 Running scheduled daily verification...")
                    self.run_full_verification()
                    last_daily_run = current_time
                else:
                    # Regular batch processing
                    self.process_batch()
                
                time.sleep(self.sleep_interval)
                
            except KeyboardInterrupt:
                logger.info("⛔ Received shutdown signal")
                self.stop()
            except Exception as e:
                logger.error(f"❌ Error in scheduled worker: {e}", exc_info=True)
                time.sleep(self.sleep_interval)
    
    def run_full_verification(self):
        """Run full verification of all unverified emails"""
        db = SessionLocal()
        
        try:
            service = EmailVerificationService(db)
            
            unverified_count = db.query(Email).filter(
                Email.verified == False
            ).count()
            
            logger.info(f"📊 Starting full verification of {unverified_count} emails")
            
            total_verified = 0
            total_invalid = 0
            
            while True:
                result = service.verify_unverified_emails(limit=100)
                
                if result['total'] == 0:
                    break
                
                total_verified += result['verified']
                total_invalid += result['invalid']
                
                logger.info(f"   Progress: {total_verified + total_invalid} emails processed")
                
                # Small delay between batches to avoid overwhelming mail servers
                time.sleep(5)
            
            logger.info(f"✅ Full verification complete:")
            logger.info(f"   Total verified: {total_verified}")
            logger.info(f"   Total invalid: {total_invalid}")
            
        except Exception as e:
            logger.error(f"❌ Error in full verification: {e}", exc_info=True)
        finally:
            db.close()


def main():
    """Main entry point"""
    import sys
    
    worker_type = sys.argv[1] if len(sys.argv) > 1 else "continuous"
    
    if worker_type == "scheduled":
        worker = ScheduledVerificationWorker(batch_size=50)
    else:
        worker = EmailVerificationWorker(batch_size=50, sleep_interval=60)
    
    worker.run()


if __name__ == "__main__":
    main()