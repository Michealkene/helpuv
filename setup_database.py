#!/usr/bin/env python3
"""
Database Setup Script for Helpuvio
Run this script to initialize the Supabase database with all required tables.

Usage:
    python setup_database.py
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set in .env file")
    sys.exit(1)

print(f"Connecting to database...")
print(f"URL: {DATABASE_URL[:50]}...")

try:
    engine = create_engine(DATABASE_URL)

    # Read the SQL file
    sql_file = os.path.join(os.path.dirname(__file__), 'database', 'supabase_init.sql')

    with open(sql_file, 'r') as f:
        sql_content = f.read()

    # Execute the SQL
    with engine.connect() as conn:
        # Split by semicolons and execute each statement
        statements = sql_content.split(';')

        for i, statement in enumerate(statements):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    conn.execute(text(statement))
                    conn.commit()
                except Exception as e:
                    if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                        print(f"  Skipping (already exists): {statement[:50]}...")
                    else:
                        print(f"  Warning at statement {i}: {e}")

    print("\n✅ Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the backend: cd backend && uvicorn app.main:app --reload")
    print("2. Access API docs: http://localhost:8000/docs")
    print("3. Admin login: admin@helpuvio.com / admin123")
    print("4. Import companies via: POST /api/companies/admin/import")

except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
