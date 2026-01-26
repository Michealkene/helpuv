"""
CSV Importer Service - Fast bulk import with email verification
"""

import pandas as pd
import asyncio
import logging
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.company import Company, ImportBatch, EmailVerificationJob, EmailVerificationStatus
from app.schemas.company import CSV_COLUMN_MAPPING

logger = logging.getLogger(__name__)


class CSVImporter:
    """
    Fast CSV importer for company data.
    Handles your specific CSV format with automatic field mapping.
    """

    BATCH_SIZE = 1000  # Insert in batches for performance
    EXPECTED_COLUMNS = set(CSV_COLUMN_MAPPING.keys())

    def __init__(self, db: Session):
        self.db = db
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

    async def import_csv(
        self,
        file: BinaryIO,
        filename: str,
        admin_id: UUID,
        dataset_id: Optional[int] = None,
        auto_verify: bool = True
    ) -> ImportBatch:
        """
        Import companies from CSV file.

        Args:
            file: File-like object containing CSV data
            filename: Original filename
            admin_id: Admin who triggered the import
            dataset_id: Optional dataset to associate companies with
            auto_verify: Whether to queue emails for verification

        Returns:
            ImportBatch with import statistics
        """
        # Create import batch record
        batch = ImportBatch(
            id=uuid4(),
            filename=filename,
            imported_by=admin_id,
            dataset_id=dataset_id,
            status="processing",
            started_at=datetime.utcnow()
        )
        self.db.add(batch)
        self.db.commit()

        try:
            # Read CSV with pandas
            df = pd.read_csv(file, dtype=str, keep_default_na=False)
            df.columns = df.columns.str.strip().str.lower()

            batch.total_rows = len(df)
            batch.file_size_bytes = file.seek(0, 2)  # Get file size
            file.seek(0)  # Reset file pointer

            self.db.commit()

            # Validate columns
            self._validate_columns(df)

            # Process in batches
            companies_to_insert = []
            verification_jobs = []
            imported = 0
            failed = 0
            skipped = 0

            for idx, row in df.iterrows():
                try:
                    company = self._process_row(row, batch.id, dataset_id)

                    if company is None:
                        skipped += 1
                        continue

                    companies_to_insert.append(company)

                    # Queue for email verification if has email
                    if company.has_email and auto_verify:
                        job = EmailVerificationJob(
                            company_id=company.id,
                            email=company.email,
                            status="pending"
                        )
                        verification_jobs.append(job)

                    imported += 1

                    # Batch insert
                    if len(companies_to_insert) >= self.BATCH_SIZE:
                        self.db.bulk_save_objects(companies_to_insert)
                        self.db.bulk_save_objects(verification_jobs)
                        self.db.commit()

                        # Update batch progress
                        batch.imported_rows = imported
                        batch.failed_rows = failed
                        batch.skipped_rows = skipped
                        batch.pending_verification = len(verification_jobs)
                        self.db.commit()

                        companies_to_insert = []
                        verification_jobs = []

                except Exception as e:
                    failed += 1
                    self.errors.append({
                        "row": idx + 2,  # +2 for header and 0-indexing
                        "error": str(e),
                        "data": row.to_dict() if hasattr(row, 'to_dict') else str(row)
                    })
                    logger.warning(f"Row {idx + 2} failed: {e}")

            # Insert remaining companies
            if companies_to_insert:
                self.db.bulk_save_objects(companies_to_insert)
                self.db.bulk_save_objects(verification_jobs)
                self.db.commit()

            # Update batch final stats
            batch.imported_rows = imported
            batch.failed_rows = failed
            batch.skipped_rows = skipped
            batch.pending_verification = self.db.query(EmailVerificationJob).filter(
                EmailVerificationJob.company_id.in_(
                    self.db.query(Company.id).filter(Company.import_batch_id == batch.id)
                ),
                EmailVerificationJob.status == "pending"
            ).count()
            batch.status = "completed"
            batch.completed_at = datetime.utcnow()

            if self.errors:
                batch.error_details = {"errors": self.errors[:100]}  # Store first 100 errors

            self.db.commit()

            logger.info(f"Import completed: {imported} imported, {failed} failed, {skipped} skipped")
            return batch

        except Exception as e:
            batch.status = "failed"
            batch.error_message = str(e)
            batch.completed_at = datetime.utcnow()
            self.db.commit()
            logger.error(f"Import failed: {e}")
            raise

    def _validate_columns(self, df: pd.DataFrame):
        """Validate CSV has required columns"""
        csv_columns = set(df.columns)
        missing = {"company"} - csv_columns  # Only company name is required

        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        unknown = csv_columns - self.EXPECTED_COLUMNS
        if unknown:
            self.warnings.append({
                "type": "unknown_columns",
                "columns": list(unknown),
                "message": f"Unknown columns will be ignored: {unknown}"
            })

    def _process_row(self, row: pd.Series, batch_id: UUID, dataset_id: Optional[int]) -> Optional[Company]:
        """
        Process a single CSV row into a Company object.
        Returns None if row should be skipped.
        """
        company_name = self._get_value(row, "company")

        if not company_name or company_name.strip() == "":
            return None  # Skip rows without company name

        # Parse emails
        email = self._get_value(row, "email")
        emails_raw = self._get_value(row, "emails")
        emails = self._parse_array(emails_raw) if emails_raw else []

        # Parse phones
        phone = self._get_value(row, "phone")
        phones_raw = self._get_value(row, "phones")
        phones = self._parse_array(phones_raw) if phones_raw else []

        # Determine if has email/phone
        has_email = bool(email and email.strip() and "@" in email)
        has_phone = bool(phone and phone.strip())

        # Skip companies with neither email nor phone
        if not has_email and not has_phone:
            return None

        # Parse numeric fields safely
        rating = self._parse_float(self._get_value(row, "rating"))
        reviews = self._parse_int(self._get_value(row, "reviews"))
        employee_count = self._parse_int(self._get_value(row, "employee_count"))
        founded_year = self._parse_int(self._get_value(row, "founded_year"))
        performance_score = self._parse_float(self._get_value(row, "performance_score"))
        response_time_ms = self._parse_int(self._get_value(row, "response_time_ms"))

        # Parse sent as boolean
        sent_raw = self._get_value(row, "sent")
        sent = sent_raw.lower() in ("true", "1", "yes") if sent_raw else False

        # Use locality as city if city not provided
        locality = self._get_value(row, "locality")
        city = locality  # They're the same in your format

        company = Company(
            id=uuid4(),
            company_name=company_name.strip(),
            category=self._get_value(row, "category"),
            group_name=self._get_value(row, "group"),

            # Contact
            email=email.strip().lower() if email else None,
            emails=emails,
            phone=phone.strip() if phone else None,
            phones=phones,

            # Address
            street=self._get_value(row, "street"),
            locality=locality,
            city=city,
            state=self._get_value(row, "state"),
            zip_code=self._get_value(row, "zip"),
            country=self._get_value(row, "country"),

            # Online
            website=self._get_value(row, "website"),
            linkedin_url=self._get_value(row, "linkedin_url"),
            twitter_url=self._get_value(row, "twitter_url"),
            facebook_url=self._get_value(row, "facebook_url"),
            instagram_url=self._get_value(row, "instagram_url"),
            socials=self._get_value(row, "socials"),

            # Business
            ceo_name=self._get_value(row, "ceo_name"),
            description=self._get_value(row, "description"),
            meta_title=self._get_value(row, "meta_title"),
            employee_count=employee_count,
            founded_year=founded_year,
            rating=rating,
            reviews=reviews,

            # Media
            avatar_url=self._get_value(row, "avatar_url"),
            favicon_url=self._get_value(row, "favicon_url"),

            # Crawl metadata
            performance_score=performance_score,
            response_time_ms=response_time_ms,
            crawl_status=self._get_value(row, "crawl_status"),
            crawl_error=self._get_value(row, "crawl_error"),
            sent=sent,

            # Flags
            has_email=has_email,
            has_phone=has_phone,
            has_verified_email=False,

            # Verification status
            email_verification_status=EmailVerificationStatus.PENDING if has_email else None,

            # Display control (will be updated after verification)
            # Phone-only companies are immediately displayable
            is_displayable=has_phone and not has_email,

            # Tracking
            import_batch_id=batch_id,
            dataset_id=dataset_id
        )

        return company

    def _get_value(self, row: pd.Series, key: str) -> Optional[str]:
        """Safely get a value from the row"""
        if key in row.index:
            val = row[key]
            if pd.isna(val) or val == "" or val == "nan":
                return None
            return str(val).strip()
        return None

    def _parse_array(self, value: str) -> List[str]:
        """Parse comma or pipe separated values into array"""
        if not value:
            return []

        # Try different separators
        if "|" in value:
            items = value.split("|")
        elif "," in value:
            items = value.split(",")
        else:
            items = [value]

        return [item.strip() for item in items if item.strip()]

    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        """Safely parse integer"""
        if not value:
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def _parse_float(self, value: Optional[str]) -> Optional[float]:
        """Safely parse float"""
        if not value:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


class ImportStatsService:
    """Service for import statistics and progress tracking"""

    def __init__(self, db: Session):
        self.db = db

    def get_batch_progress(self, batch_id: UUID) -> Dict[str, Any]:
        """Get current progress of an import batch"""
        batch = self.db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
        if not batch:
            return None

        # Get verification progress
        verification_stats = self.db.query(
            EmailVerificationJob.status,
            func.count(EmailVerificationJob.id)
        ).filter(
            EmailVerificationJob.company_id.in_(
                self.db.query(Company.id).filter(Company.import_batch_id == batch_id)
            )
        ).group_by(EmailVerificationJob.status).all()

        verification_progress = {status: count for status, count in verification_stats}

        progress_percent = 0
        if batch.total_rows > 0:
            progress_percent = (batch.imported_rows / batch.total_rows) * 100

        current_phase = "importing"
        if batch.status == "completed":
            pending_jobs = verification_progress.get("pending", 0) + verification_progress.get("processing", 0)
            if pending_jobs > 0:
                current_phase = "verifying"
            else:
                current_phase = "completed"

        return {
            "batch_id": batch.id,
            "status": batch.status,
            "total_rows": batch.total_rows,
            "imported_rows": batch.imported_rows,
            "failed_rows": batch.failed_rows,
            "skipped_rows": batch.skipped_rows,
            "progress_percent": progress_percent,
            "current_phase": current_phase,
            "verification_progress": verification_progress
        }

    def get_verification_stats(self, batch_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get overall verification statistics"""
        query = self.db.query(Company)

        if batch_id:
            query = query.filter(Company.import_batch_id == batch_id)

        total = query.count()
        with_email = query.filter(Company.has_email == True).count()

        verified = query.filter(
            Company.email_verification_status == EmailVerificationStatus.VERIFIED
        ).count()

        invalid = query.filter(
            Company.email_verification_status == EmailVerificationStatus.INVALID
        ).count()

        catch_all = query.filter(
            Company.email_verification_status == EmailVerificationStatus.CATCH_ALL
        ).count()

        pending = query.filter(
            Company.email_verification_status == EmailVerificationStatus.PENDING
        ).count()

        unknown = query.filter(
            Company.email_verification_status == EmailVerificationStatus.UNKNOWN
        ).count()

        verification_rate = (verified / with_email * 100) if with_email > 0 else 0

        return {
            "total_companies": total,
            "total_with_email": with_email,
            "verified": verified,
            "invalid": invalid,
            "catch_all": catch_all,
            "pending": pending,
            "unknown": unknown,
            "verification_rate": round(verification_rate, 2)
        }
