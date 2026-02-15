"""Start API server on Windows VPS via batch + schtasks"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8')
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('3.231.147.217', username='Administrator', password=r'Y;Y$aJloHykJxnxueYuVvwD0e7$RS!Ya', timeout=30)
print("Connected!")

def run(cmd, t=30):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=t)
    try:
        out = stdout.read().decode('utf-8', errors='replace').strip()
    except:
        out = ""
    return out

# Kill existing
print("[1] Kill existing...")
run('taskkill /F /IM python.exe 2>nul')
time.sleep(4)

# Write a batch file that starts the API
print("[2] Writing start_api.bat...")
sftp = ssh.open_sftp()
with sftp.open('/xaubot_engine/start_api.bat', 'w') as f:
    f.write('@echo off\r\ncd /d C:\\xaubot_engine\r\n"C:\\Program Files\\Python311\\python.exe" api_server.py\r\n')
sftp.close()

# Use schtasks to run it NOW (runs as background task)
print("[3] Creating and running scheduled task...")
run('schtasks /Delete /TN "XAUBOT_API_RUN" /F 2>nul')
time.sleep(1)
run('schtasks /Create /TN "XAUBOT_API_RUN" /TR "C:\\xaubot_engine\\start_api.bat" /SC ONCE /ST 00:00 /RU Administrator /RP "Y;Y$aJloHykJxnxueYuVvwD0e7$RS!Ya" /F')
time.sleep(1)
run('schtasks /Run /TN "XAUBOT_API_RUN"')
print("  Task triggered!")

time.sleep(10)

# Check
print("[4] Checking port...")
out = run('netstat -an | findstr 5001')
print(f"  {out or 'Not found'}")

# Also create auto-start and daily trade tasks
print("[5] Creating persistent tasks...")
run('schtasks /Create /TN "XAUBOT_API_BOOT" /TR "C:\\xaubot_engine\\start_api.bat" /SC ONSTART /RU SYSTEM /F')
run('schtasks /Create /TN "XAUBOT_DAILY_TRADE" /TR "\"C:\\Program Files\\Python311\\python.exe\" C:\\xaubot_engine\\engine.py" /SC DAILY /ST 04:05 /RU SYSTEM /F')

# Firewall
print("[6] Firewall...")
run('netsh advfirewall firewall add rule name="XAUBOT5001" dir=in action=allow protocol=TCP localport=5001 2>nul')

print("\nDone!")
ssh.close()
