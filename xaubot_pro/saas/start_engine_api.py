"""Start the API server on Windows VPS"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8')
import paramiko

HOST = "3.231.147.217"
USER = "Administrator"
PASS = r"Y;Y$aJloHykJxnxueYuVvwD0e7$RS!Ya"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)
print("Connected!")

def run(cmd, label=""):
    if label: print(f"  {label}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(f"    {out[:500]}")
    if err: print(f"    [err] {err[:300]}")
    return out

# Kill any existing python on 5001
print("[1] Stopping existing processes...")
run('taskkill /F /IM python.exe 2>nul', 'Killing python...')
time.sleep(3)

# Start API server
print("[2] Starting API server...")
run(
    'start /B "XAUBOT" "C:\\Program Files\\Python311\\python.exe" C:\\xaubot_engine\\api_server.py > C:\\xaubot_engine\\api.log 2>&1',
    'Launching...'
)
time.sleep(8)

# Check
print("[3] Verifying...")
run('netstat -an | findstr 5001', 'Port 5001:')
run('type C:\\xaubot_engine\\api.log', 'Log:')

ssh.close()
print("\nDone!")
