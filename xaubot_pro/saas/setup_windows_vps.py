"""Install Python and start trading engine on Windows VPS"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import paramiko

HOST = "3.231.147.217"
USER = "Administrator"
PASS = r"Y;Y$aJloHykJxnxueYuVvwD0e7$RS!Ya"

print("=" * 60)
print("XAUBOT Pro - Windows VPS Setup")
print("=" * 60)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)
print("Connected!")

def run(cmd, label="", timeout=180):
    if label: print(f"  {label}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(f"    {out[:800]}")
    if err and 'WARNING' not in err and 'already' not in err.lower():
        print(f"    [err] {err[:400]}")
    return out

# Step 1: Download Python installer
print("\n[1] Downloading Python 3.11...")
run(
    'powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe -OutFile C:\\python_installer.exe"',
    'Downloading...', timeout=300
)

# Step 2: Install Python silently
print("\n[2] Installing Python 3.11...")
run(
    'C:\\python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0',
    'Installing (this takes a minute)...', timeout=300
)
time.sleep(15)

# Step 3: Verify Python
print("\n[3] Verifying Python...")
# Need to use full path since PATH may not be refreshed in this SSH session
python_paths = [
    'C:\\Program Files\\Python311\\python.exe',
    'C:\\Python311\\python.exe',
    'C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python311\\python.exe',
]
python_exe = None
for p in python_paths:
    out = run(f'if exist "{p}" echo FOUND')
    if 'FOUND' in out:
        python_exe = p
        print(f"    Python found at: {p}")
        break

if not python_exe:
    # Try to find it
    out = run('where /R C:\\ python.exe 2>nul', 'Searching for python.exe...')
    if out:
        python_exe = out.split('\n')[0].strip()
        print(f"    Found: {python_exe}")
    else:
        print("    ERROR: Python not found after install. Trying PATH...")
        run('set PATH', 'Checking PATH...')
        # Try refreshing
        out = run('"C:\\Program Files\\Python311\\python.exe" --version 2>nul || "C:\\Python311\\python.exe" --version 2>nul')
        if 'Python' in out:
            python_exe = '"C:\\Program Files\\Python311\\python.exe"' if 'Program' in out else '"C:\\Python311\\python.exe"'

if not python_exe:
    print("  FATAL: Cannot find Python. Try installing manually via RDP.")
    ssh.close()
    sys.exit(1)

run(f'"{python_exe}" --version', 'Python version:')

# Step 4: Install pip packages
print("\n[4] Installing Python packages...")
pip_exe = python_exe.replace('python.exe', 'Scripts\\pip.exe')
run(f'"{python_exe}" -m pip install --upgrade pip', 'Upgrading pip...', timeout=120)
run(f'"{python_exe}" -m pip install MetaTrader5 flask flask-cors cryptography requests pandas', 'Installing packages...', timeout=300)

# Step 5: Start API server
print("\n[5] Starting API server...")
# Create a proper start script using the found python path
start_script = f'''@echo off
cd /d C:\\xaubot_engine
"{python_exe}" api_server.py
'''
# Write start script
sftp = ssh.open_sftp()
with sftp.open('/xaubot_engine/start_api.bat', 'w') as f:
    f.write(start_script)

run_script = f'''@echo off
cd /d C:\\xaubot_engine
"{python_exe}" engine.py
pause
'''
with sftp.open('/xaubot_engine/run_trades.bat', 'w') as f:
    f.write(run_script)
sftp.close()

# Start in background
run(f'cd C:\\xaubot_engine && start /B "{python_exe}" api_server.py > C:\\xaubot_engine\\api.log 2>&1', 'Starting...')
time.sleep(8)

# Step 6: Check if running
print("\n[6] Verifying API server...")
run('netstat -an | findstr 5001', 'Port 5001:')
run('type C:\\xaubot_engine\\api.log', 'API log:')

# Step 7: Firewall
print("\n[7] Firewall...")
run('netsh advfirewall firewall add rule name="XAUBOT API 5001" dir=in action=allow protocol=TCP localport=5001', 'Opening port 5001...')

print("\n" + "=" * 60)
print("SETUP COMPLETE!")
print(f"  Python: {python_exe}")
print(f"  API: http://{HOST}:5001")
print(f"  Files: C:\\xaubot_engine\\")
print("=" * 60)

ssh.close()
