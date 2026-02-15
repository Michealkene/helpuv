"""Check which ports are open on Windows VPS from Linux VPS"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import paramiko

# Connect to Linux VPS and scan Windows VPS ports from there
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('74.50.87.77', username='root', timeout=15)
print("Connected to Linux VPS")

ports = [22, 80, 443, 3389, 5000, 5001, 8000, 8080, 8443, 8501, 3000]
for port in ports:
    stdin, stdout, stderr = ssh.exec_command(f'timeout 3 bash -c "echo > /dev/tcp/3.231.147.217/{port}" 2>&1 && echo "PORT {port} OPEN" || echo "PORT {port} CLOSED"', timeout=10)
    out = stdout.read().decode().strip()
    print(f"  {out}")

ssh.close()
