"""
Automated CSV Import Script for Helpuvio
Imports all CSV files into the database and creates datasets
"""
import sys
sys.path.insert(0, "/app")

import csv
import uuid
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.company import Company
from app.models.cart import CartItem
from app.models.dataset import Dataset, Category
from app.services.storage_service import StorageService
import asyncio

# CSV Import Configuration
CSV_FOLDER = Path("/app/app/csv_data")
BATCH_SIZE = 500  # Insert companies in batches

def slugify(text):
    """Convert text to URL-friendly slug"""
    import re
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")

def detect_enrichment_level(companies):
    """Detect if dataset has emails or just phones"""
    has_email = 0
    has_phone = 0

    for company in companies[:100]:  # Check first 100
        if company.get("email"):
            has_email += 1
        if company.get("phone"):
            has_phone += 1

    # If more than 50% have email, consider it email_and_phone
    if has_email > 50:
        return "email_and_phone"
    else:
        return "phone_only"

def calculate_price(company_count, enrichment_level):
    """Calculate dataset price based on count and enrichment"""
    price_per_company = 5 if enrichment_level == "phone_only" else 10  # cents
    return company_count * price_per_company

def parse_csv_file(filepath):
    """Parse CSV file and return companies list"""
    companies = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                company = {
                    "id": str(uuid.uuid4()),
                    "company_name": row.get("company", row.get("name", row.get("company_name", ""))),
                    "category": row.get("categories", row.get("category", "")),
                    "state": row.get("state", ""),
                    "phone": row.get("phone", ""),
                    "email": row.get("email", ""),
                    "website": row.get("website", ""),
                    "linkedin_url": row.get("linkedin_url", ""),
                    "twitter_url": row.get("twitter_url", ""),
                    "facebook_url": row.get("facebook_url", ""),
                    "instagram_url": row.get("instagram_url", ""),
                    "description": row.get("description", ""),
                }

                # Only add if has company name
                if company["company_name"]:
                    companies.append(company)

        print(f"✓ Parsed {len(companies)} companies from {filepath.name}")
        return companies

    except Exception as e:
        print(f"✗ Error parsing {filepath.name}: {e}")
        return []

async def upload_csv_to_storage(filepath, storage_service):
    """Upload CSV file to R2 storage"""
    try:
        with open(filepath, "rb") as f:
            csv_content = f.read()

        filename = f"{uuid.uuid4()}.csv"
        file_path = await storage_service.upload_csv(csv_content, filename)

        print(f"✓ Uploaded {filepath.name} to R2 storage: {file_path}")
        return file_path

    except Exception as e:
        print(f"✗ Failed to upload {filepath.name}: {e}")
        return None

def import_companies_batch(db, companies, dataset_id):
    """Import companies in batches for better performance"""
    total = len(companies)
    imported = 0

    for i in range(0, total, BATCH_SIZE):
        batch = companies[i:i + BATCH_SIZE]

        company_objects = []
        for comp_data in batch:
            company = Company(
                id=comp_data["id"],
                dataset_id=dataset_id,
                company_name=comp_data["company_name"],
                category=comp_data["category"],
                state=comp_data["state"],
                phone=comp_data["phone"],
                email=comp_data["email"],
                website=comp_data["website"],
                linkedin_url=comp_data["linkedin_url"],
                twitter_url=comp_data["twitter_url"],
                facebook_url=comp_data["facebook_url"],
                instagram_url=comp_data["instagram_url"],
                description=comp_data["description"],
            )
            company_objects.append(company)

        db.bulk_save_objects(company_objects)
        db.commit()

        imported += len(batch)
        print(f"  Imported {imported}/{total} companies ({imported/total*100:.1f}%)")

    return imported

async def process_csv_file(filepath, db, storage_service):
    """Process a single CSV file: parse, upload, create dataset"""
    print(f"\n{'='*60}")
    print(f"Processing: {filepath.name}")
    print(f"{'='*60}")

    # Parse CSV
    companies = parse_csv_file(filepath)
    if not companies:
        print(f"✗ Skipping {filepath.name} - no valid companies found")
        return False

    # Detect enrichment level
    enrichment_level = detect_enrichment_level(companies)
    company_count = len(companies)

    # Calculate price
    price_cents = calculate_price(company_count, enrichment_level)

    # Upload to R2
    csv_file_path = await upload_csv_to_storage(filepath, storage_service)
    if not csv_file_path:
        print(f"✗ Skipping {filepath.name} - upload failed")
        return False

    # Get or create category (using first category from data)
    category_name = "Business Leads"
    if companies[0]["category"]:
        category_name = companies[0]["category"].split(",")[0].strip()

    category = db.query(Category).filter(Category.name == category_name).first()
    if not category:
        category = Category(
            name=category_name,
            slug=slugify(category_name),
            description=f"{category_name} business contacts"
        )
        db.add(category)
        db.commit()
        db.refresh(category)

    # Create dataset name from filename
    dataset_name = filepath.stem.replace("_", " ").title()
    dataset_slug = slugify(dataset_name)

    # Create dataset
    dataset = Dataset(
        name=dataset_name,
        slug=dataset_slug,
        description=f"Verified {enrichment_level.replace('_', ' ')} dataset with {company_count} companies",
        category_id=category.id,
        location="United States",
        company_count=company_count,
        enrichment_level=enrichment_level,
        price_cents=price_cents,
        csv_file_path=csv_file_path,
        is_published=True,
        total_purchases=0,
        total_revenue_cents=0,
        last_updated_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    print(f"✓ Created dataset: {dataset.name} (ID: {dataset.id})")
    print(f"  - Companies: {company_count}")
    print(f"  - Enrichment: {enrichment_level}")
    print(f"  - Price: ${price_cents/100:.2f}")

    # Import companies
    print(f"\nImporting companies...")
    imported = import_companies_batch(db, companies, dataset.id)

    print(f"✅ Successfully imported {imported} companies")
    return True

async def main():
    """Main import function"""
    print("\n" + "="*60)
    print("Helpuvio CSV Import Script")
    print("="*60)

    # Find all CSV files
    csv_files = list(CSV_FOLDER.glob("*.csv"))
    csv_files = [f for f in csv_files if f.name != "import_csvs.py"]

    if not csv_files:
        print("No CSV files found in /var/www/csv_import/")
        return

    print(f"\nFound {len(csv_files)} CSV files to import:")
    for f in csv_files:
        print(f"  - {f.name}")

    print("\nStarting import...")

    # Initialize services
    db = SessionLocal()
    storage_service = StorageService()

    if not storage_service.is_configured:
        print("✗ Storage service not configured. Check R2 credentials.")
        return

    # Process each CSV file
    success_count = 0
    failed_count = 0

    for filepath in csv_files:
        try:
            success = await process_csv_file(filepath, db, storage_service)
            if success:
                success_count += 1
            else:
                failed_count += 1
        except Exception as e:
            print(f"✗ Critical error processing {filepath.name}: {e}")
            failed_count += 1
            import traceback
            traceback.print_exc()

    db.close()

    # Summary
    print("\n" + "="*60)
    print("Import Complete!")
    print("="*60)
    print(f"Successfully imported: {success_count} files")
    print(f"Failed: {failed_count} files")
    print(f"\nDatasets are now available at https://helpuvio.com/datasets")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
