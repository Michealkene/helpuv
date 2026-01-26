"""
SMTP Email Verification Service with Worker Support
Verifies emails using MX lookup and SMTP handshake
"""

import asyncio
import socket
import smtplib
import dns.resolver
import logging
import re
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.company import Company, EmailVerificationJob, EmailVerificationStatus
from app.core.config import settings

logger = logging.getLogger(__name__)


class SMTPEmailVerifier:
    """
    Verifies email addresses using SMTP protocol.
    Uses MX lookup and SMTP handshake to validate deliverability.
    """

    # Email regex for basic format validation
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    # Common disposable email domains to reject
    DISPOSABLE_DOMAINS = {
        'tempmail.com', 'throwaway.email', 'mailinator.com',
        'guerrillamail.com', 'temp-mail.org', '10minutemail.com'
    }

    # Timeout settings (seconds)
    DNS_TIMEOUT = 10
    SMTP_TIMEOUT = 30

    def __init__(self, from_email: Optional[str] = None, from_domain: Optional[str] = None):
        """
        Initialize verifier with sender details.

        Args:
            from_email: Email address used in SMTP MAIL FROM (for verification)
            from_domain: Domain used in HELO command
        """
        self.from_email = from_email or settings.SMTP_VERIFY_FROM_EMAIL or "verify@helpuvio.com"
        self.from_domain = from_domain or settings.SMTP_VERIFY_DOMAIN or "helpuvio.com"

    def validate_format(self, email: str) -> bool:
        """Check if email has valid format"""
        if not email or len(email) > 254:
            return False
        return bool(self.EMAIL_REGEX.match(email.lower()))

    def is_disposable(self, email: str) -> bool:
        """Check if email is from a disposable domain"""
        domain = email.lower().split('@')[-1]
        return domain in self.DISPOSABLE_DOMAINS

    async def get_mx_records(self, domain: str) -> List[Tuple[int, str]]:
        """
        Get MX records for domain, sorted by priority.
        Returns list of (priority, mx_host) tuples.
        """
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = self.DNS_TIMEOUT
            resolver.lifetime = self.DNS_TIMEOUT

            mx_records = resolver.resolve(domain, 'MX')
            records = [(record.preference, str(record.exchange).rstrip('.'))
                      for record in mx_records]
            return sorted(records, key=lambda x: x[0])

        except dns.resolver.NXDOMAIN:
            logger.debug(f"No MX records found for {domain}")
            return []
        except dns.resolver.NoAnswer:
            logger.debug(f"No MX answer for {domain}")
            return []
        except dns.resolver.Timeout:
            logger.warning(f"DNS timeout for {domain}")
            return []
        except Exception as e:
            logger.error(f"DNS error for {domain}: {e}")
            return []

    def _smtp_verify_sync(self, email: str, mx_host: str) -> Tuple[str, str]:
        """
        Synchronous SMTP verification (runs in thread pool).
        Returns (status, response) tuple.
        """
        try:
            # Connect to SMTP server
            smtp = smtplib.SMTP(timeout=self.SMTP_TIMEOUT)
            smtp.connect(mx_host, 25)

            # Send HELO
            code, message = smtp.helo(self.from_domain)
            if code != 250:
                smtp.quit()
                return "unknown", f"HELO rejected: {code} {message}"

            # Send MAIL FROM
            code, message = smtp.mail(self.from_email)
            if code != 250:
                smtp.quit()
                return "unknown", f"MAIL FROM rejected: {code} {message}"

            # Send RCPT TO (the actual verification)
            code, message = smtp.rcpt(email)
            response = f"{code} {message.decode() if isinstance(message, bytes) else message}"

            smtp.quit()

            # Interpret response
            if code == 250:
                return "verified", response
            elif code == 251:
                # User not local; will forward
                return "verified", response
            elif code == 252:
                # Cannot verify, but will accept
                return "catch_all", response
            elif code in (450, 451, 452):
                # Temporary failure - mailbox may exist
                return "unknown", response
            elif code in (550, 551, 552, 553, 554):
                # Permanent failure - mailbox doesn't exist
                return "invalid", response
            else:
                return "unknown", response

        except smtplib.SMTPConnectError as e:
            return "unknown", f"Connection failed: {e}"
        except smtplib.SMTPServerDisconnected as e:
            return "unknown", f"Server disconnected: {e}"
        except socket.timeout:
            return "unknown", "SMTP timeout"
        except socket.error as e:
            return "unknown", f"Socket error: {e}"
        except Exception as e:
            logger.error(f"SMTP error for {email}: {e}")
            return "unknown", f"Error: {e}"

    async def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verify a single email address.

        Returns dict with:
            - status: verified, invalid, catch_all, unknown
            - mx_record: primary MX server used
            - smtp_response: SMTP server response
            - error: error message if any
        """
        email = email.lower().strip()

        # Basic format check
        if not self.validate_format(email):
            return {
                "status": EmailVerificationStatus.INVALID,
                "error": "Invalid email format",
                "mx_record": None,
                "smtp_response": None
            }

        # Check disposable
        if self.is_disposable(email):
            return {
                "status": EmailVerificationStatus.INVALID,
                "error": "Disposable email domain",
                "mx_record": None,
                "smtp_response": None
            }

        domain = email.split('@')[-1]

        # Get MX records
        mx_records = await self.get_mx_records(domain)

        if not mx_records:
            return {
                "status": EmailVerificationStatus.INVALID,
                "error": "No MX records found",
                "mx_record": None,
                "smtp_response": None
            }

        # Try each MX server in priority order
        last_error = None
        for priority, mx_host in mx_records:
            try:
                # Run SMTP verification in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    status, response = await loop.run_in_executor(
                        executor,
                        self._smtp_verify_sync,
                        email,
                        mx_host
                    )

                if status == "verified":
                    return {
                        "status": EmailVerificationStatus.VERIFIED,
                        "mx_record": mx_host,
                        "smtp_response": response,
                        "error": None
                    }
                elif status == "invalid":
                    return {
                        "status": EmailVerificationStatus.INVALID,
                        "mx_record": mx_host,
                        "smtp_response": response,
                        "error": None
                    }
                elif status == "catch_all":
                    return {
                        "status": EmailVerificationStatus.CATCH_ALL,
                        "mx_record": mx_host,
                        "smtp_response": response,
                        "error": None
                    }
                else:
                    last_error = response
                    continue  # Try next MX server

            except Exception as e:
                last_error = str(e)
                continue

        # All MX servers failed or returned unknown
        return {
            "status": EmailVerificationStatus.UNKNOWN,
            "mx_record": mx_records[0][1] if mx_records else None,
            "smtp_response": last_error,
            "error": last_error
        }


class EmailVerificationWorker:
    """
    Worker that processes email verification jobs from the queue.
    Can run multiple concurrent verifications.
    """

    def __init__(self, db: Session, worker_id: Optional[str] = None, max_concurrent: int = 10):
        self.db = db
        self.worker_id = worker_id or f"worker-{uuid4().hex[:8]}"
        self.max_concurrent = max_concurrent
        self.verifier = SMTPEmailVerifier()
        self.running = False
        self._stop_event = asyncio.Event()

    async def start(self):
        """Start the worker"""
        self.running = True
        self._stop_event.clear()
        logger.info(f"Worker {self.worker_id} started with {self.max_concurrent} concurrent jobs")

        while self.running:
            try:
                # Get batch of jobs
                jobs = self._claim_jobs(self.max_concurrent)

                if not jobs:
                    # No jobs available, wait a bit
                    await asyncio.sleep(5)
                    continue

                # Process jobs concurrently
                tasks = [self._process_job(job) for job in jobs]
                await asyncio.gather(*tasks, return_exceptions=True)

            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(5)

            # Check if stop was requested
            if self._stop_event.is_set():
                break

        logger.info(f"Worker {self.worker_id} stopped")

    def stop(self):
        """Signal worker to stop"""
        self.running = False
        self._stop_event.set()

    def _claim_jobs(self, limit: int) -> List[EmailVerificationJob]:
        """Claim pending jobs for this worker"""
        now = datetime.utcnow()
        lock_timeout = now - timedelta(minutes=5)  # Release stale locks

        # Find and claim pending jobs
        jobs = self.db.query(EmailVerificationJob).filter(
            and_(
                EmailVerificationJob.status.in_(["pending", "processing"]),
                EmailVerificationJob.attempts < EmailVerificationJob.max_attempts,
                # Only take if not locked or lock expired
                (EmailVerificationJob.locked_at == None) |
                (EmailVerificationJob.locked_at < lock_timeout)
            )
        ).limit(limit).with_for_update(skip_locked=True).all()

        # Lock jobs for this worker
        for job in jobs:
            job.status = "processing"
            job.worker_id = self.worker_id
            job.locked_at = now
            job.attempts += 1

        self.db.commit()
        return jobs

    async def _process_job(self, job: EmailVerificationJob):
        """Process a single verification job"""
        try:
            # Verify the email
            result = await self.verifier.verify_email(job.email)

            # Update job
            job.status = "completed"
            job.result = result["status"].value if hasattr(result["status"], 'value') else result["status"]
            job.mx_record = result.get("mx_record")
            job.smtp_response = result.get("smtp_response")
            job.error_message = result.get("error")
            job.processed_at = datetime.utcnow()

            # Update company
            company = self.db.query(Company).filter(Company.id == job.company_id).first()
            if company:
                company.email_verification_status = result["status"]
                company.email_verified_at = datetime.utcnow() if result["status"] == EmailVerificationStatus.VERIFIED else None
                company.email_verification_error = result.get("error")
                company.email_mx_record = result.get("mx_record")
                company.email_smtp_response = result.get("smtp_response")
                company.update_displayable_status()

            self.db.commit()

            logger.debug(f"Verified {job.email}: {result['status']}")

        except Exception as e:
            logger.error(f"Job failed for {job.email}: {e}")
            job.status = "pending" if job.attempts < job.max_attempts else "failed"
            job.error_message = str(e)
            self.db.commit()


class VerificationManager:
    """
    Manages email verification workers and jobs.
    """

    def __init__(self, db: Session):
        self.db = db
        self.workers: List[EmailVerificationWorker] = []

    async def start_workers(self, num_workers: int = 3, max_concurrent_per_worker: int = 10):
        """Start multiple verification workers"""
        for i in range(num_workers):
            worker = EmailVerificationWorker(
                self.db,
                worker_id=f"worker-{i+1}",
                max_concurrent=max_concurrent_per_worker
            )
            self.workers.append(worker)
            asyncio.create_task(worker.start())

        logger.info(f"Started {num_workers} verification workers")

    def stop_workers(self):
        """Stop all workers"""
        for worker in self.workers:
            worker.stop()
        self.workers.clear()

    def queue_verification(
        self,
        company_ids: Optional[List[UUID]] = None,
        batch_id: Optional[UUID] = None
    ) -> int:
        """
        Queue companies for email verification.

        Args:
            company_ids: Specific companies to verify
            batch_id: Verify all companies in import batch

        Returns:
            Number of jobs queued
        """
        query = self.db.query(Company).filter(
            Company.has_email == True,
            Company.email_verification_status == EmailVerificationStatus.PENDING
        )

        if company_ids:
            query = query.filter(Company.id.in_(company_ids))

        if batch_id:
            query = query.filter(Company.import_batch_id == batch_id)

        companies = query.all()

        jobs_created = 0
        for company in companies:
            # Check if job already exists
            existing = self.db.query(EmailVerificationJob).filter(
                EmailVerificationJob.company_id == company.id,
                EmailVerificationJob.status.in_(["pending", "processing"])
            ).first()

            if not existing:
                job = EmailVerificationJob(
                    company_id=company.id,
                    email=company.email,
                    status="pending"
                )
                self.db.add(job)
                jobs_created += 1

        self.db.commit()
        logger.info(f"Queued {jobs_created} verification jobs")
        return jobs_created

    def get_worker_status(self) -> Dict[str, Any]:
        """Get status of all workers"""
        # Get job stats
        pending = self.db.query(EmailVerificationJob).filter(
            EmailVerificationJob.status == "pending"
        ).count()

        processing = self.db.query(EmailVerificationJob).filter(
            EmailVerificationJob.status == "processing"
        ).count()

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        completed_today = self.db.query(EmailVerificationJob).filter(
            EmailVerificationJob.status == "completed",
            EmailVerificationJob.processed_at >= today_start
        ).count()

        # Calculate average verification time
        avg_time = self.db.query(
            func.avg(
                func.extract('epoch', EmailVerificationJob.processed_at) -
                func.extract('epoch', EmailVerificationJob.created_at)
            )
        ).filter(
            EmailVerificationJob.status == "completed",
            EmailVerificationJob.processed_at >= today_start
        ).scalar()

        return {
            "total_workers": len(self.workers),
            "active_workers": sum(1 for w in self.workers if w.running),
            "jobs_pending": pending,
            "jobs_processing": processing,
            "jobs_completed_today": completed_today,
            "avg_verification_time_ms": int(avg_time * 1000) if avg_time else None
        }


# Singleton instance for background workers
_verification_manager: Optional[VerificationManager] = None


def get_verification_manager(db: Session) -> VerificationManager:
    """Get or create verification manager"""
    global _verification_manager
    if _verification_manager is None:
        _verification_manager = VerificationManager(db)
    return _verification_manager
