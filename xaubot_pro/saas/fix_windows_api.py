"""Fix and start API server on Windows VPS using scheduled task"""
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

def run(cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(f"  {out[:600]}")
    if err and 'WARNING' not in err: print(f"  [err] {err[:300]}")
    return out

# Re-upload api_server.py with 0.0.0.0 binding
print("[1] Uploading fixed api_server.py...")
sftp = ssh.open_sftp()
import os
local = os.path.join(os.path.dirname(__file__), 'engine', 'api_server.py')
sftp.put(local, '/xaubot_engine/api_server.py')
sftp.close()
print("  Uploaded!")

# Kill existing
print("[2] Killing existing python...")
run('taskkill /F /IM python.exe 2>nul')
time.sleep(5)

# Create a VBS launcher (workaround for start /B not working via SSH)
print("[3] Creating launcher...")
run('''powershell -Command "Set-Content -Path C:\\xaubot_engine\\launch_api.vbs -Value 'Set WshShell = CreateObject(\"WScript.Shell\") : WshShell.Run \"\"\"C:\\Program Files\\Python311\\python.exe\"\" C:\\xaubot_engine\\api_server.py\", 0, False'"''')

# Launch via VBS (runs hidden, no window)
print("[4] Starting API server...")
run('cscript //nologo C:\\xaubot_engine\\launch_api.vbs')
time.sleep(8)

# Verify
print("[5] Checking port 5001...")
out = run('netstat -an | findstr 5001')
if '5001' in out and 'LISTENING' in out:
    print("  API SERVER IS RUNNING!")
else:
    print("  Not listening yet. Trying direct start...")
    run('"C:\\Program Files\\Python311\\python.exe" C:\\xaubot_engine\\api_server.py &')
    time.sleep(5)
    out = run('netstat -an | findstr 5001')
    if 'LISTENING' in out:
        print("  API SERVER IS RUNNING!")
    else:
        print("  Still not listening. Check manually via RDP.")

# Create scheduled task for auto-start on boot
print("[6] Creating auto-start scheduled task...")
run('schtasks /Create /TN "XAUBOT_API" /TR "cscript //nologo C:\\xaubot_engine\\launch_api.vbs" /SC ONSTART /RU SYSTEM /F')

# Create daily trade task (4:05 AM UTC)
print("[7] Creating daily trade task...")
run('''schtasks /Create /TN "XAUBOT_TRADES" /TR "\"C:\\Program Files\\Python311\\python.exe\" C:\\xaubot_engine\\engine.py" /SC DAILY /ST 04:05 /RU SYSTEM /F''')

print("\nDone!")
ssh.close()
