#!/usr/bin/env python3
"""
Create datasets from existing company data
Groups companies by state and category
"""

import psycopg2
from datetime import datetime
import random

# Database connection
DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/helpuvio'

def create_datasets():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Get category mapping
        category_map = {
            'Painting Contractors': 12,      # construction
            'Flooring Contractors': 12,      # construction
            'Roofing Contractors': 12,       # construction
            'Water Damage Restoration': 7,   # services
            'Pool Services': 7,              # services
            'Interior Designers': 7,         # services
            'Paving Contractors': 12,        # construction
            'Trash Pickup': 7,               # services
            'Drain Cleaning': 7,             # services
            'Cabinet Refinishing': 7,        # services
            'Water Heater Repair': 7,        # services
            'Mold Inspection': 7             # services
        }

        # Get companies grouped by state and category
        cur.execute("""
            SELECT state, category, COUNT(*) as count
            FROM companies
            WHERE state IS NOT NULL
            AND category IS NOT NULL
            AND LENGTH(state) = 2  -- Only 2-letter state codes
            GROUP BY state, category
            HAVING COUNT(*) >= 50  -- Only create datasets with 50+ companies
            ORDER BY COUNT(*) DESC
        """)

        groups = cur.fetchall()

        print(f"Found {len(groups)} potential datasets to create")

        created = 0
        for state, category, count in groups:
            # Get category_id
            category_id = category_map.get(category, 7)  # Default to services

            # Create dataset name
            dataset_name = f"{state} {category}"
            dataset_slug = f"{state.lower()}-{category.lower().replace(' ', '-')}"

            # Create location string
            location = f"{state}, USA"

            # Set pricing based on enrichment level (simplified)
            price_cents = 5000  # $50
            enrichment_level = 'phone_only'

            description = f"Verified database of {count} {category} in {state}. Includes contact information, business details, and location data."

            # Check if dataset already exists
            cur.execute("SELECT id FROM datasets WHERE slug = %s", (dataset_slug,))
            if cur.fetchone():
                print(f"  ⏭️  Skipping {dataset_name} - already exists")
                continue

            # Insert dataset
            cur.execute("""
                INSERT INTO datasets (
                    name, slug, description, category_id, location,
                    company_count, enrichment_level, price_cents,
                    is_published, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW(), NOW())
                RETURNING id
            """, (
                dataset_name, dataset_slug, description, category_id, location,
                count, enrichment_level, price_cents
            ))

            dataset_id = cur.fetchone()[0]

            # Update companies to link to this dataset
            cur.execute("""
                UPDATE companies
                SET dataset_id = %s
                WHERE state = %s AND category = %s
            """, (dataset_id, state, category))

            created += 1
            print(f"  ✅ Created: {dataset_name} ({count} companies)")

        conn.commit()
        print(f"\n🎉 Successfully created {created} datasets!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_datasets()
