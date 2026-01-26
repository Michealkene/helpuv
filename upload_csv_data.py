#!/usr/bin/env python3
"""
CSV Data Uploader for Helpuvio Database
Uploads company data from CSV files to PostgreSQL database
"""

import os
import sys
import csv
import uuid
from datetime import datetime
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
import argparse

# Load environment variables
load_dotenv('/var/www/helpuvio/.env')

# Database connection - Use local PostgreSQL container
DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/helpuvio'  # Local Docker PostgreSQL

class CSVUploader:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(DATABASE_URL)
            self.cursor = self.conn.cursor()
            print("✓ Connected to database")
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            sys.exit(1)

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")

    def parse_array_field(self, value: str) -> List[str]:
        """Parse comma-separated string into array"""
        if not value or value.strip() == '':
            return []
        # Split by comma and clean up
        items = [item.strip() for item in value.split(',')]
        return [item for item in items if item]

    def process_row(self, row: Dict[str, str], dataset_id: int = None) -> Dict[str, Any]:
        """Process a CSV row and extract required fields"""

        # Extract company name (prioritize 'company' field)
        company_name = row.get('company', '').strip()
        if not company_name:
            company_name = row.get('website', '').strip()

        # Website
        website = row.get('website', '').strip()

        # Email handling
        email = row.get('email', '').strip()
        emails_str = row.get('emails', '').strip()
        emails_list = self.parse_array_field(emails_str)

        # If no primary email but have emails array, use first one
        if not email and emails_list:
            email = emails_list[0]

        # Phone handling
        phone = row.get('phone', '').strip()
        phones_str = row.get('phones', '').strip()
        phones_list = self.parse_array_field(phones_str)

        # If no primary phone but have phones array, use first one
        if not phone and phones_list:
            phone = phones_list[0]

        # Address
        street = row.get('street', '').strip()
        city = row.get('locality', '').strip()  # CSV uses 'locality' for city
        country = row.get('country', '').strip()
        state = row.get('state', '').strip()
        zip_code = row.get('zip', '').strip()

        # Category
        category = row.get('category', '').strip()

        # Additional fields (optional)
        group_name = row.get('group', '').strip()
        linkedin_url = row.get('linkedin_url', '').strip()
        twitter_url = row.get('twitter_url', '').strip()
        facebook_url = row.get('facebook_url', '').strip()
        instagram_url = row.get('instagram_url', '').strip()
        socials = row.get('socials', '').strip()
        ceo_name = row.get('ceo_name', '').strip()
        description = row.get('description', '').strip()
        meta_title = row.get('meta_title', '').strip()
        avatar_url = row.get('avatar_url', '').strip()
        favicon_url = row.get('favicon_url', '').strip()

        # Numeric fields
        rating = float(row.get('rating', 0)) if row.get('rating', '').strip() else None
        reviews = int(row.get('reviews', 0)) if row.get('reviews', '').strip() else None
        employee_count = int(row.get('employee_count', 0)) if row.get('employee_count', '').strip() else None
        founded_year = int(row.get('founded_year', 0)) if row.get('founded_year', '').strip() else None
        performance_score = float(row.get('performance_score', 0)) if row.get('performance_score', '').strip() else None
        response_time_ms = int(row.get('response_time_ms', 0)) if row.get('response_time_ms', '').strip() else None

        # Crawl status
        crawl_status = row.get('crawl_status', '').strip()
        crawl_error = row.get('crawl_error', '').strip()
        sent = row.get('sent', '').strip().lower() in ['true', '1', 'yes']

        # Set has_email and has_phone flags
        has_email = bool(email)
        has_phone = bool(phone)

        # Build data dict
        data = {
            'id': str(uuid.uuid4()),
            'company_name': company_name,
            'website': website,
            'email': email if email else None,
            'emails': emails_list,
            'phone': phone if phone else None,
            'phones': phones_list,
            'street': street if street else None,
            'locality': city,
            'city': city,
            'state': state if state else None,
            'zip_code': zip_code if zip_code else None,
            'country': country if country else None,
            'category': category if category else None,
            'group_name': group_name if group_name else None,
            'linkedin_url': linkedin_url if linkedin_url else None,
            'twitter_url': twitter_url if twitter_url else None,
            'facebook_url': facebook_url if facebook_url else None,
            'instagram_url': instagram_url if instagram_url else None,
            'socials': socials if socials else None,
            'ceo_name': ceo_name if ceo_name else None,
            'description': description if description else None,
            'meta_title': meta_title if meta_title else None,
            'avatar_url': avatar_url if avatar_url else None,
            'favicon_url': favicon_url if favicon_url else None,
            'rating': rating,
            'reviews': reviews,
            'employee_count': employee_count,
            'founded_year': founded_year,
            'performance_score': performance_score,
            'response_time_ms': response_time_ms,
            'crawl_status': crawl_status if crawl_status else None,
            'crawl_error': crawl_error if crawl_error else None,
            'sent': sent,
            'has_email': has_email,
            'has_phone': has_phone,
            'dataset_id': dataset_id,
            'email_verification_status': 'pending',
            'is_displayable': False
        }

        return data

    def insert_companies(self, companies: List[Dict[str, Any]]) -> int:
        """Insert companies into database"""

        insert_query = """
        INSERT INTO companies (
            id, company_name, website, email, emails, phone, phones,
            street, locality, city, state, zip_code, country, category, group_name,
            linkedin_url, twitter_url, facebook_url, instagram_url, socials,
            ceo_name, description, meta_title, avatar_url, favicon_url,
            rating, reviews, employee_count, founded_year,
            performance_score, response_time_ms, crawl_status, crawl_error, sent,
            has_email, has_phone, dataset_id, email_verification_status, is_displayable,
            created_at, updated_at
        ) VALUES (
            %(id)s, %(company_name)s, %(website)s, %(email)s, %(emails)s, %(phone)s, %(phones)s,
            %(street)s, %(locality)s, %(city)s, %(state)s, %(zip_code)s, %(country)s, %(category)s, %(group_name)s,
            %(linkedin_url)s, %(twitter_url)s, %(facebook_url)s, %(instagram_url)s, %(socials)s,
            %(ceo_name)s, %(description)s, %(meta_title)s, %(avatar_url)s, %(favicon_url)s,
            %(rating)s, %(reviews)s, %(employee_count)s, %(founded_year)s,
            %(performance_score)s, %(response_time_ms)s, %(crawl_status)s, %(crawl_error)s, %(sent)s,
            %(has_email)s, %(has_phone)s, %(dataset_id)s, %(email_verification_status)s, %(is_displayable)s,
            NOW(), NOW()
        )
        ON CONFLICT (id) DO NOTHING
        """

        try:
            execute_batch(self.cursor, insert_query, companies, page_size=100)
            self.conn.commit()
            return len(companies)
        except Exception as e:
            self.conn.rollback()
            print(f"✗ Insert failed: {e}")
            raise

    def upload_csv(self, csv_file: str, dataset_id: int = None, batch_size: int = 100):
        """Upload CSV file to database"""

        if not os.path.exists(csv_file):
            print(f"✗ File not found: {csv_file}")
            return

        print(f"\n📁 Processing: {csv_file}")
        print(f"{'='*60}")

        companies = []
        total_rows = 0
        inserted_rows = 0
        skipped_rows = 0

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=1):
                    total_rows += 1

                    # Skip rows without company name
                    if not row.get('company', '').strip() and not row.get('website', '').strip():
                        skipped_rows += 1
                        continue

                    try:
                        company_data = self.process_row(row, dataset_id)
                        companies.append(company_data)

                        # Insert in batches
                        if len(companies) >= batch_size:
                            inserted = self.insert_companies(companies)
                            inserted_rows += inserted
                            print(f"  ✓ Inserted batch: {inserted} companies (Total: {inserted_rows})")
                            companies = []

                    except Exception as e:
                        print(f"  ✗ Row {row_num} error: {e}")
                        skipped_rows += 1
                        continue

                # Insert remaining companies
                if companies:
                    inserted = self.insert_companies(companies)
                    inserted_rows += inserted
                    print(f"  ✓ Inserted final batch: {inserted} companies")

            # Summary
            print(f"\n{'='*60}")
            print(f"📊 Summary:")
            print(f"  Total rows:    {total_rows}")
            print(f"  Inserted:      {inserted_rows}")
            print(f"  Skipped:       {skipped_rows}")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"✗ Upload failed: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description='Upload CSV data to Helpuvio database')
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('--dataset-id', type=int, help='Dataset ID to associate companies with')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for inserts (default: 100)')

    args = parser.parse_args()

    uploader = CSVUploader()

    try:
        uploader.connect()
        uploader.upload_csv(args.csv_file, args.dataset_id, args.batch_size)
    except Exception as e:
        print(f"\n✗ Upload failed: {e}")
        sys.exit(1)
    finally:
        uploader.close()

    print("✓ Upload completed successfully!")


if __name__ == "__main__":
    main()
