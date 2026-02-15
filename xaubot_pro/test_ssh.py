import paramiko, sys, socket
sys.stdout.reconfigure(encoding='utf-8')

host = "3.231.147.217"
print(f"Testing SSH to {host}...")

# Test raw socket first
for port in [22, 3389, 80, 443]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((host, port))
        print(f"  Port {port}: OPEN")
        s.close()
    except socket.timeout:
        print(f"  Port {port}: TIMEOUT")
    except ConnectionRefusedError:
        print(f"  Port {port}: REFUSED (host reachable but port closed)")
    except Exception as e:
        print(f"  Port {port}: {e}")

# Try SSH
print("\nAttempting SSH connection...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(host, username="Administrator", password=r"Y;Y$aJloHykJxnxueYuVvwD0e7$RS!Ya", timeout=10)
    print("  SSH Connected!")
    stdin, stdout, stderr = ssh.exec_command("whoami")
    print(f"  whoami: {stdout.read().decode().strip()}")
    ssh.close()
except Exception as e:
    print(f"  SSH Failed: {e}")
