import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://74.50.87.77"

tests = [
    ("Landing Page", f"{BASE}/", "XAUBOT"),
    ("Checkout Page", f"{BASE}/checkout", "XAUBOT Pro"),
    ("Admin Panel", f"{BASE}/admin?admin_key=xaubot_admin_2026", "Admin Panel"),
]

print("=" * 50)
print("XAUBOT Pro - Deployment Verification")
print("=" * 50)

for name, url, expect in tests:
    try:
        r = urllib.request.urlopen(url, timeout=10)
        data = r.read(1000).decode('utf-8', errors='replace')
        ok = expect in data
        print(f"  [{('OK' if ok else 'WARN')}] {name}: {r.status} {'(content match)' if ok else '(no match)'}")
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")

# Test API
print()
print("API Tests:")
try:
    # Create affiliate
    data = json.dumps({"name": "TestInfluencer", "email": "test@test.com"}).encode()
    req = urllib.request.Request(f"{BASE}/api/affiliate/create", data=data,
        headers={"Content-Type": "application/json", "X-Admin-Key": "xaubot_admin_2026"})
    r = urllib.request.urlopen(req, timeout=10)
    result = json.loads(r.read().decode())
    print(f"  [OK] Create Affiliate: ref_code={result.get('ref_code')}, link={result.get('ref_link')}")
except Exception as e:
    print(f"  [FAIL] Create Affiliate: {e}")

try:
    # Create order
    data = json.dumps({"email": "buyer@test.com", "ref_code": ""}).encode()
    req = urllib.request.Request(f"{BASE}/api/order/create", data=data,
        headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=15)
    result = json.loads(r.read().decode())
    print(f"  [OK] Create Order: id={result.get('order_id')}, btc={result.get('amount_btc')}, addr={result.get('btc_address')}")
except Exception as e:
    print(f"  [FAIL] Create Order: {e}")

try:
    # List affiliates
    req = urllib.request.Request(f"{BASE}/api/affiliate/list",
        headers={"X-Admin-Key": "xaubot_admin_2026"})
    r = urllib.request.urlopen(req, timeout=10)
    result = json.loads(r.read().decode())
    print(f"  [OK] List Affiliates: {len(result)} affiliates")
except Exception as e:
    print(f"  [FAIL] List Affiliates: {e}")

print()
print("=" * 50)
print("URLS:")
print(f"  Landing:  {BASE}")
print(f"  Checkout: {BASE}/checkout")
print(f"  Admin:    {BASE}/admin?admin_key=xaubot_admin_2026")
print(f"  Domain:   http://xaubotpro.74.50.87.77.sslip.io")
print("=" * 50)
