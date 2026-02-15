"""Deploy trading engine to Windows VPS via SSH/Paramiko"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import paramiko

HOST = "3.231.147.217"
USER = "Administrator"
PASS = r"Y;Y$aJloHykJxnxueYuVvwD0e7$RS!Ya"
ENGINE_DIR = os.path.join(os.path.dirname(__file__), 'engine')
WEB_DIR = os.path.join(os.path.dirname(__file__), 'web')

print("=" * 60)
print("XAUBOT Pro - Deploy Trading Engine to Windows VPS")
print("=" * 60)

# Connect
print(f"\n[1] Connecting to {HOST}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(HOST, username=USER, password=PASS, timeout=30)
    print("  Connected!")
except Exception as e:
    print(f"  FAILED: {e}")
    sys.exit(1)

def run(cmd, label=""):
    if label: print(f"  {label}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(f"    {out[:500]}")
    if err and 'WARNING' not in err: print(f"    [err] {err[:300]}")
    return out

def upload(local_path, remote_path):
    sftp = ssh.open_sftp()
    sftp.put(local_path, remote_path)
    sftp.close()
    print(f"  Uploaded: {os.path.basename(local_path)} -> {remote_path}")

# Create directory
print("\n[2] Creating directories...")
run('if not exist C:\\xaubot_engine mkdir C:\\xaubot_engine', 'Creating C:\\xaubot_engine')

# Upload files
print("\n[3] Uploading engine files...")
files_to_upload = [
    (os.path.join(ENGINE_DIR, 'engine.py'), '/xaubot_engine/engine.py'),
    (os.path.join(ENGINE_DIR, 'worker.py'), '/xaubot_engine/worker.py'),
    (os.path.join(ENGINE_DIR, 'api_server.py'), '/xaubot_engine/api_server.py'),
    (os.path.join(ENGINE_DIR, 'requirements.txt'), '/xaubot_engine/requirements.txt'),
    (os.path.join(WEB_DIR, 'encryption.py'), '/xaubot_engine/encryption.py'),
    (os.path.join(WEB_DIR, 'models.py'), '/xaubot_engine/models.py'),
]

sftp = ssh.open_sftp()
for local, remote in files_to_upload:
    try:
        remote_win = f"C:{remote}"
        sftp.put(local, remote)
        print(f"  OK: {os.path.basename(local)}")
    except Exception as e:
        print(f"  FAIL: {os.path.basename(local)} - {e}")
sftp.close()

# Check Python
print("\n[4] Checking Python...")
out = run('python --version')
if 'Python' not in out:
    out = run('python3 --version')
    if 'Python' not in out:
        print("  WARNING: Python not found. You need to install Python.")

# Install dependencies
print("\n[5] Installing Python dependencies...")
run('pip install MetaTrader5 flask flask-cors cryptography requests pandas --quiet', 'Installing packages...')

# Check MT5
print("\n[6] Checking MetaTrader 5...")
run('if exist "C:\\Program Files\\MetaTrader 5\\terminal64.exe" (echo MT5 FOUND) else (echo MT5 NOT FOUND)')

# Create startup script
print("\n[7] Creating startup scripts...")
startup_script = '''@echo off
cd /d C:\\xaubot_engine
echo Starting XAUBOT Trading Engine API...
echo Press Ctrl+C to stop.
python api_server.py
'''
stdin, stdout, stderr = ssh.exec_command('echo @echo off > C:\\xaubot_engine\\start_api.bat')
stdout.read()

# Write via echo
cmds = [
    'echo @echo off > C:\\xaubot_engine\\start_api.bat',
    'echo cd /d C:\\xaubot_engine >> C:\\xaubot_engine\\start_api.bat',
    'echo python api_server.py >> C:\\xaubot_engine\\start_api.bat',
]
for c in cmds:
    run(c)

# Start the API server in background
print("\n[8] Starting API server...")
run('cd C:\\xaubot_engine && start /B python api_server.py > C:\\xaubot_engine\\api.log 2>&1', 'Launching api_server.py...')

import time
time.sleep(5)

# Verify
print("\n[9] Verifying...")
run('netstat -an | findstr 5001', 'Checking port 5001...')
run('type C:\\xaubot_engine\\api.log', 'API log:')

# Open firewall
print("\n[10] Opening firewall port 5001...")
run('netsh advfirewall firewall add rule name="XAUBOT API" dir=in action=allow protocol=TCP localport=5001', 'Adding firewall rule...')

print("\n" + "=" * 60)
print("DEPLOYMENT COMPLETE!")
print("=" * 60)
print(f"  API Server: http://{HOST}:5001")
print(f"  Files: C:\\xaubot_engine\\")
print("=" * 60)

ssh.close()
