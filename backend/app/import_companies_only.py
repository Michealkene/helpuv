"""
Import companies to existing datasets
"""
import sys
sys.path.insert(0, "/app")

import csv
import uuid
from pathlib import Path
from app.core.database import SessionLocal
from app.models.company import Company
from app.models.dataset import Dataset
from app.models.cart import CartItem

CSV_FOLDER = Path("/app/app/csv_data")
BATCH_SIZE = 1000

def parse_csv_file(filepath):
    """Parse CSV and return companies"""
    companies = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                company = {
                    "id": str(uuid.uuid4()),
                    "company_name": (row.get("company", row.get("name", row.get("company_name", ""))) or "")[:500],
                    "category": (row.get("categories", row.get("category", "")) or "")[:255],
                    "state": (row.get("state", "") or "")[:255],
                    "phone": (row.get("phone", "") or "")[:100],
                    "email": (row.get("email", "") or "")[:255],
                    "website": (row.get("website", "") or "")[:500],
                    "linkedin_url": (row.get("linkedin_url", "") or "")[:500],
                    "twitter_url": (row.get("twitter_url", "") or "")[:500],
                    "facebook_url": (row.get("facebook_url", "") or "")[:500],
                    "instagram_url": (row.get("instagram_url", "") or "")[:500],
                    "description": (row.get("description", "") or "")[:2000],
                }
                if company["company_name"]:
                    companies.append(company)
        print(f"✓ Parsed {len(companies)} companies")
        return companies
    except Exception as e:
        print(f"✗ Error: {e}")
        return []

def import_companies_batch(db, companies, dataset_id):
    """Import companies in batches"""
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
        print(f"  Imported {imported}/{total} ({imported/total*100:.1f}%)")

    return imported

def main():
    print("\n" + "="*60)
    print("Importing Companies to Existing Datasets")
    print("="*60)

    db = SessionLocal()

    # Get all datasets
    datasets = db.query(Dataset).all()
    print(f"\nFound {len(datasets)} datasets")

    # Map CSV files to datasets by slug
    csv_files = list(CSV_FOLDER.glob("*.csv"))

    for dataset in datasets:
        # Find matching CSV file
        csv_file = None
        for f in csv_files:
            if dataset.slug in f.stem.lower().replace("_", "").replace("-", ""):
                csv_file = f
                break
            elif f.stem.lower().replace("_", "-") == dataset.slug:
                csv_file = f
                break

        if not csv_file:
            print(f"\n✗ No CSV found for dataset: {dataset.name}")
            continue

        print(f"\n{'='*60}")
        print(f"Dataset: {dataset.name} (ID: {dataset.id})")
        print(f"CSV: {csv_file.name}")
        print(f"{'='*60}")

        # Parse and import
        companies = parse_csv_file(csv_file)
        if companies:
            imported = import_companies_batch(db, companies, dataset.id)
            print(f"✅ Imported {imported} companies to {dataset.name}")
        else:
            print(f"✗ No companies to import")

    db.close()

    # Final stats
    db2 = SessionLocal()
    total_companies = db2.query(Company).count()
    db2.close()

    print("\n" + "="*60)
    print(f"Import Complete!")
    print(f"Total companies in database: {total_companies:,}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
