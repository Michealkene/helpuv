import socket, sys
sys.stdout.reconfigure(encoding='utf-8')
host = "74.50.87.77"
print(f"Testing {host}...")
for port in [22, 80, 443, 3389, 8501, 5985, 8080, 8000]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((host, port))
        print(f"  Port {port}: OPEN")
        s.close()
    except socket.timeout:
        print(f"  Port {port}: TIMEOUT")
    except ConnectionRefusedError:
        print(f"  Port {port}: REFUSED (host up, port closed)")
    except Exception as e:
        print(f"  Port {port}: {e}")
print("Done.")
