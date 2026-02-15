import urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE = "http://74.50.87.77"
pages = [
    "/", "/best-gold-trading-bot", "/automated-xauusd-trading",
    "/gold-trading-bot-for-beginners", "/trading-bot-affiliate-program",
    "/forex-robot-gold-2026", "/sitemap.xml", "/robots.txt", "/checkout"
]
print("SEO Page Verification:")
for p in pages:
    try:
        r = urllib.request.urlopen(f"{BASE}{p}", timeout=10)
        data = r.read(200).decode('utf-8', errors='replace')
        print(f"  [OK] {p} -> {r.status}")
    except Exception as e:
        print(f"  [FAIL] {p} -> {e}")
