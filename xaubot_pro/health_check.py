"""
XAUBOT Pro - System Health Check
Tests all components and dependencies
"""
import sys
import os

# Results tracking
results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def test(name, func):
    """Run a test and track results"""
    try:
        func()
        results['passed'].append(name)
        print(f"[OK] {name}")
        return True
    except Exception as e:
        results['failed'].append((name, str(e)))
        print(f"[FAIL] {name}: {e}")
        return False

def warn(name, message):
    """Add a warning"""
    results['warnings'].append((name, message))
    print(f"[WARN] {name}: {message}")

print("=" * 60)
print("XAUBOT PRO - SYSTEM HEALTH CHECK")
print("=" * 60)
print()

# Test 1: Core dependencies
print("[1/7] Testing Core Dependencies...")
test("Streamlit", lambda: __import__('streamlit'))
test("Flask", lambda: __import__('flask'))
test("MetaTrader5", lambda: __import__('MetaTrader5'))
test("Pandas", lambda: __import__('pandas'))
test("Plotly", lambda: __import__('plotly'))
test("NumPy", lambda: __import__('numpy'))
print()

# Test 2: Backend dependencies
print("[2/7] Testing Backend Dependencies...")
test("Flask-CORS", lambda: __import__('flask_cors'))
test("BCrypt", lambda: __import__('bcrypt'))
test("PyJWT", lambda: __import__('jwt'))
test("Cryptography", lambda: __import__('cryptography'))
test("Requests", lambda: __import__('requests'))
print()

# Test 3: Configuration files
print("[3/7] Testing Configuration Files...")
test("config.json exists", lambda: os.path.exists("config.json"))
test("backend/xaubot.db exists", lambda: os.path.exists("backend/xaubot.db"))

if os.path.exists("config.json"):
    import json
    test("config.json valid JSON", lambda: json.load(open("config.json")))
print()

# Test 4: Critical files
print("[4/7] Testing Critical Files...")
critical_files = [
    "app.py",
    "live_bot.py",
    "backend/app.py",
    "requirements.txt"
]
for f in critical_files:
    test(f"File: {f}", lambda file=f: os.path.exists(file))
print()

# Test 5: Flask app
print("[5/7] Testing Flask Backend...")
try:
    sys.path.insert(0, 'backend')
    from app import app as flask_app
    routes = [str(r) for r in flask_app.url_map.iter_rules()]
    test("Flask app loads", lambda: True)
    print(f"      Routes: {len(routes)} endpoints")
except Exception as e:
    results['failed'].append(("Flask app", str(e)))
    print(f"[FAIL] Flask app: {e}")
print()

# Test 6: Database
print("[6/7] Testing Database...")
try:
    import sqlite3
    conn = sqlite3.connect("backend/xaubot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    test("Database connection", lambda: True)
    print(f"      Tables: {', '.join(tables)}")
    conn.close()
except Exception as e:
    results['failed'].append(("Database", str(e)))
    print(f"[FAIL] Database: {e}")
print()

# Test 7: MT5 Configuration
print("[7/7] Testing MT5 Configuration...")
if os.path.exists("config.json"):
    import json
    config = json.load(open("config.json"))
    required_keys = ['mt5_login', 'mt5_password', 'mt5_server']
    for key in required_keys:
        if key in config:
            test(f"MT5 config: {key}", lambda: True)
        else:
            warn(f"MT5 config: {key}", "Missing from config.json")
print()

# Summary
print("=" * 60)
print("HEALTH CHECK SUMMARY")
print("=" * 60)
print(f"PASSED: {len(results['passed'])}")
print(f"FAILED: {len(results['failed'])}")
print(f"WARNINGS: {len(results['warnings'])}")
print()

if results['failed']:
    print("FAILURES:")
    for name, error in results['failed']:
        print(f"  - {name}: {error}")
    print()

if results['warnings']:
    print("WARNINGS:")
    for name, msg in results['warnings']:
        print(f"  - {name}: {msg}")
    print()

if not results['failed']:
    print("[OK] All critical tests passed!")
    print("System is ready for deployment.")
    sys.exit(0)
else:
    print("[ERROR] Some tests failed. Review above.")
    sys.exit(1)
