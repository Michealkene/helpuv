#!/usr/bin/env python3
"""
Reset admin password script
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from passlib.context import CryptContext
import psycopg2
from urllib.parse import urlparse

# Password hashing context (same as in the app)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

# Database connection from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:helpuvio2024@postgres:5432/helpuvio')

# Parse the database URL
result = urlparse(DATABASE_URL)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

print("Resetting admin password...")
print(f"Connecting to database: {hostname}:{port}/{database}")

# Admin credentials
admin_email = "admin@helpuvio.com"
new_password = "changeme123"

# Hash the password
password_hash = hash_password(new_password)

try:
    # Connect to database
    conn = psycopg2.connect(
        host=hostname,
        port=port,
        user=username,
        password=password,
        database=database
    )
    cursor = conn.cursor()

    # Update admin password
    cursor.execute(
        "UPDATE admin_users SET password_hash = %s WHERE email = %s",
        (password_hash, admin_email)
    )

    rows_affected = cursor.rowcount
    conn.commit()

    if rows_affected > 0:
        print(f"✅ Password updated successfully for {admin_email}")
        print(f"\nLogin credentials:")
        print(f"  Email: {admin_email}")
        print(f"  Password: {new_password}")
        print(f"\n⚠️  IMPORTANT: Change this password immediately after logging in!")
    else:
        print(f"❌ No admin user found with email: {admin_email}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
