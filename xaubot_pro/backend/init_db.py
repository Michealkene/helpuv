"""
Initialize XauBot Pro Backend Database
Creates all required tables for affiliate program, payments, and licenses
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xaubot.db")

def init_database():
    """Create all database tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Affiliates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS affiliates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            affiliate_code TEXT UNIQUE NOT NULL,
            total_referrals INTEGER DEFAULT 0,
            total_earnings REAL DEFAULT 0.0,
            btc_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Licenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            referred_by TEXT,
            btc_transaction TEXT
        )
    ''')
    
    # Payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            amount_usd REAL NOT NULL,
            amount_btc REAL NOT NULL,
            btc_address TEXT NOT NULL,
            transaction_id TEXT,
            status TEXT DEFAULT 'pending',
            affiliate_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            license_key TEXT
        )
    ''')
    
    # Referrals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            affiliate_code TEXT NOT NULL,
            referred_email TEXT NOT NULL,
            commission_usd REAL NOT NULL,
            commission_btc REAL,
            status TEXT DEFAULT 'pending',
            paid_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default settings
    cursor.execute('''
        INSERT OR IGNORE INTO settings (key, value) VALUES
        ('product_price_usd', '297'),
        ('affiliate_commission', '0.20'),
        ('btc_wallet', 'YOUR_BTC_ADDRESS_HERE'),
        ('admin_email', 'admin@xaubot.com')
    ''')
    
    conn.commit()
    
    # Print table summary
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("[OK] Database initialized successfully")
    print(f"[OK] Location: {DB_PATH}")
    print(f"[OK] Tables created: {', '.join(tables)}")
    
    # Print counts
    for table in tables:
        if table != 'sqlite_sequence':
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} rows")
    
    conn.close()
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("XAUBOT PRO - DATABASE INITIALIZATION")
    print("=" * 50)
    print()
    
    if os.path.exists(DB_PATH):
        response = input(f"Database already exists at {DB_PATH}\nContinue? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            exit(0)
    
    try:
        init_database()
        print()
        print("=" * 50)
        print("Database ready for use!")
        print("=" * 50)
    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)
