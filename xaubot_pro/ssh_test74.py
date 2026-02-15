import paramiko, sys, os
sys.stdout.reconfigure(encoding='utf-8')

host = "74.50.87.77"
user = "root"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Try key-based auth first
key_paths = [
    os.path.expanduser("~/.ssh/id_rsa"),
    os.path.expanduser("~/.ssh/id_ed25519"),
    os.path.expanduser("~/.ssh/id_ecdsa"),
]

connected = False
for kp in key_paths:
    if os.path.exists(kp):
        try:
            print(f"Trying key: {kp}")
            ssh.connect(host, username=user, key_filename=kp, timeout=10)
            print("  Connected with key!")
            connected = True
            break
        except Exception as e:
            print(f"  Failed: {e}")

if not connected:
    # Try no password (key in agent)
    try:
        print("Trying SSH agent...")
        ssh.connect(host, username=user, timeout=10)
        print("  Connected!")
        connected = True
    except Exception as e:
        print(f"  Failed: {e}")

if connected:
    stdin, stdout, stderr = ssh.exec_command("uname -a && whoami && df -h / && free -m | head -3")
    print(f"\n{stdout.read().decode().strip()}")

    # Check what's running on port 8000
    stdin, stdout, stderr = ssh.exec_command("ss -tlnp | grep -E '(:8000|:80|:8501|:443)'")
    print(f"\nListening ports:\n{stdout.read().decode().strip()}")

    # Check python
    stdin, stdout, stderr = ssh.exec_command("python3 --version 2>&1")
    print(f"\nPython: {stdout.read().decode().strip()}")

    # Check what's installed
    stdin, stdout, stderr = ssh.exec_command("which nginx 2>/dev/null; which docker 2>/dev/null; pip3 --version 2>/dev/null | head -1")
    print(f"Tools: {stdout.read().decode().strip()}")

    ssh.close()
else:
    print("\nCould not connect. Need password.")
