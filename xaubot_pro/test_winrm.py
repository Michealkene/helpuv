import socket, sys
sys.stdout.reconfigure(encoding='utf-8')
host = "3.231.147.217"
for port in [5985, 5986, 445]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((host, port))
        print(f"Port {port}: OPEN")
        s.close()
    except socket.timeout:
        print(f"Port {port}: TIMEOUT")
    except ConnectionRefusedError:
        print(f"Port {port}: REFUSED")
    except Exception as e:
        print(f"Port {port}: {e}")
