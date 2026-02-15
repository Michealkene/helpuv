import urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8')
for url in ["http://74.50.87.77/llms.txt", "http://74.50.87.77/robots.txt", "http://74.50.87.77/sitemap.xml"]:
    try:
        r = urllib.request.urlopen(url, timeout=10)
        data = r.read(200).decode('utf-8', errors='replace')
        print(f"[OK] {url} -> {r.status}")
        print(f"     {data[:150]}...")
    except Exception as e:
        print(f"[FAIL] {url} -> {e}")
    print()
