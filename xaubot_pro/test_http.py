import urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8')
try:
    r = urllib.request.urlopen("http://74.50.87.77", timeout=10)
    print(f"Status: {r.status}")
    data = r.read(500).decode('utf-8', errors='replace')
    print(f"Content: {data[:500]}")
except Exception as e:
    print(f"Error: {e}")
