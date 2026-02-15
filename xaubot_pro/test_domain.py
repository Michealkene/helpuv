import urllib.request, socket, sys
sys.stdout.reconfigure(encoding='utf-8')

domain = "xaubotpro.74.50.87.77.sslip.io"
print(f"Testing domain: {domain}")

# DNS resolve
try:
    ip = socket.gethostbyname(domain)
    print(f"  DNS resolves to: {ip}")
except Exception as e:
    print(f"  DNS failed: {e}")

# HTTP test
try:
    r = urllib.request.urlopen(f"http://{domain}", timeout=10)
    data = r.read(200).decode('utf-8', errors='replace')
    print(f"  HTTP Status: {r.status}")
    if "XAUBOT" in data:
        print("  Content: XAUBOT Pro landing page confirmed!")
    else:
        print(f"  Content: {data[:100]}")
except Exception as e:
    print(f"  HTTP failed: {e}")
