"""Deploy XAUBOT Pro to Windows VPS via SSH"""
import sys, os, time
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import paramiko

HOST = "3.231.147.217"
USER = "Administrator"
PASS = r"Y;Y$aJloHykJxnxueYuVvwD0e7$RS!Ya"
DEPLOY_DIR = r"C:\XAUBOT_Pro"
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))

def run_cmd(ssh, cmd, timeout=120):
    print(f"  > {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        print(f"    {out[:500]}")
    if err and 'WARNING' not in err.upper():
        print(f"    [stderr] {err[:300]}")
    return out, err

def upload_file(sftp, local_path, remote_path):
    fname = os.path.basename(local_path)
    try:
        sftp.put(local_path, remote_path)
        print(f"  [OK] Uploaded {fname}")
    except Exception as e:
        print(f"  [ERR] {fname}: {e}")

def main():
    print("=" * 60)
    print("XAUBOT Pro - VPS DEPLOYMENT")
    print("=" * 60)
    print(f"Host: {HOST}")
    print(f"User: {USER}")
    print()

    # Connect
    print("[1/7] Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, username=USER, password=PASS, timeout=30)
        print("  [OK] Connected!")
    except Exception as e:
        print(f"  [FAIL] {e}")
        sys.exit(1)

    sftp = ssh.open_sftp()

    # Check system
    print("\n[2/7] Checking VPS system...")
    run_cmd(ssh, "systeminfo | findstr /B /C:\"OS Name\" /C:\"OS Version\"")
    run_cmd(ssh, "python --version")

    # Create deploy directory
    print(f"\n[3/7] Setting up {DEPLOY_DIR}...")
    run_cmd(ssh, f'if not exist "{DEPLOY_DIR}" mkdir "{DEPLOY_DIR}"')
    run_cmd(ssh, f'if not exist "{DEPLOY_DIR}\\.streamlit" mkdir "{DEPLOY_DIR}\\.streamlit"')
    run_cmd(ssh, f'if not exist "{DEPLOY_DIR}\\landing" mkdir "{DEPLOY_DIR}\\landing"')

    # Upload files
    print("\n[4/7] Uploading XAUBOT Pro files...")
    files_to_upload = [
        ("app.py", f"{DEPLOY_DIR}\\app.py"),
        ("live_bot.py", f"{DEPLOY_DIR}\\live_bot.py"),
        ("trade.py", f"{DEPLOY_DIR}\\trade.py"),
        ("config.json", f"{DEPLOY_DIR}\\config.json"),
        ("requirements.txt", f"{DEPLOY_DIR}\\requirements.txt"),
        (".streamlit\\config.toml", f"{DEPLOY_DIR}\\.streamlit\\config.toml"),
        ("landing\\index.html", f"{DEPLOY_DIR}\\landing\\index.html"),
        ("landing\\server.py", f"{DEPLOY_DIR}\\landing\\server.py"),
    ]

    for local_rel, remote_path in files_to_upload:
        local_full = os.path.join(LOCAL_DIR, local_rel)
        if os.path.exists(local_full):
            # Use forward slashes for SFTP
            remote_sftp = remote_path.replace("\\", "/")
            upload_file(sftp, local_full, remote_sftp)
        else:
            print(f"  [SKIP] {local_rel} not found locally")

    # Install Python if needed + dependencies
    print("\n[5/7] Installing dependencies on VPS...")
    out, _ = run_cmd(ssh, "python --version")
    if "Python" not in out:
        print("  [!] Python not found on VPS. Attempting install...")
        run_cmd(ssh, 'powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe -OutFile C:\\python_installer.exe"', timeout=120)
        run_cmd(ssh, 'C:\\python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1', timeout=180)
        run_cmd(ssh, 'setx PATH "%PATH%;C:\\Program Files\\Python311;C:\\Program Files\\Python311\\Scripts" /M')
        time.sleep(5)
        run_cmd(ssh, "python --version")

    # Create venv and install packages
    out, _ = run_cmd(ssh, f'if exist "{DEPLOY_DIR}\\.venv\\Scripts\\python.exe" (echo VENV_EXISTS) else (echo NO_VENV)')
    if "NO_VENV" in out:
        print("  Creating virtual environment...")
        run_cmd(ssh, f'python -m venv "{DEPLOY_DIR}\\.venv"', timeout=60)

    print("  Installing pip packages...")
    run_cmd(ssh, f'"{DEPLOY_DIR}\\.venv\\Scripts\\pip.exe" install --upgrade pip -q', timeout=60)
    run_cmd(ssh, f'"{DEPLOY_DIR}\\.venv\\Scripts\\pip.exe" install streamlit plotly pandas numpy -q', timeout=120)

    # Create startup scripts on VPS
    print("\n[6/7] Creating startup scripts...")

    # Landing page startup script (port 80)
    landing_bat = f"""@echo off
cd /d "{DEPLOY_DIR}\\landing"
"{DEPLOY_DIR}\\.venv\\Scripts\\python.exe" server.py 80
"""
    landing_bat_path = f"{DEPLOY_DIR}/start_landing.bat"
    with sftp.open(landing_bat_path, 'w') as f:
        f.write(landing_bat)
    print("  [OK] start_landing.bat")

    # Dashboard startup script (port 8501)
    dash_bat = f"""@echo off
cd /d "{DEPLOY_DIR}"
"{DEPLOY_DIR}\\.venv\\Scripts\\streamlit.exe" run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
"""
    dash_bat_path = f"{DEPLOY_DIR}/start_dashboard.bat"
    with sftp.open(dash_bat_path, 'w') as f:
        f.write(dash_bat)
    print("  [OK] start_dashboard.bat")

    # Master startup script
    master_bat = f"""@echo off
echo Starting XAUBOT Pro services...
start "XAUBOT Landing" /min cmd /c "{DEPLOY_DIR}\\start_landing.bat"
timeout /t 3 /nobreak >nul
start "XAUBOT Dashboard" /min cmd /c "{DEPLOY_DIR}\\start_dashboard.bat"
echo.
echo XAUBOT Pro is running:
echo   Landing page: http://3.231.147.217
echo   Dashboard:    http://3.231.147.217:8501
echo.
echo Close this window to keep services running in background.
"""
    master_bat_path = f"{DEPLOY_DIR}/start_all.bat"
    with sftp.open(master_bat_path, 'w') as f:
        f.write(master_bat)
    print("  [OK] start_all.bat")

    # Create scheduled task to auto-start on boot
    print("\n[7/7] Setting up auto-start on boot...")
    task_cmd = (
        f'schtasks /create /tn "XAUBOT_Pro" /tr "{DEPLOY_DIR}\\start_all.bat" '
        f'/sc onstart /ru Administrator /rp "{PASS}" /rl highest /f'
    )
    run_cmd(ssh, task_cmd)
    print("  [OK] Scheduled task created")

    # Open firewall ports
    print("\n  Opening firewall ports...")
    run_cmd(ssh, 'netsh advfirewall firewall add rule name="XAUBOT Landing HTTP" dir=in action=allow protocol=tcp localport=80')
    run_cmd(ssh, 'netsh advfirewall firewall add rule name="XAUBOT Dashboard" dir=in action=allow protocol=tcp localport=8501')

    # Start services now
    print("\n  Starting services...")
    run_cmd(ssh, f'start /min cmd /c "{DEPLOY_DIR}\\start_landing.bat"')
    time.sleep(2)
    run_cmd(ssh, f'start /min cmd /c "{DEPLOY_DIR}\\start_dashboard.bat"')
    time.sleep(3)

    # Verify
    print("\n  Checking if services are running...")
    run_cmd(ssh, 'netstat -an | findstr ":80 " | findstr LISTENING')
    run_cmd(ssh, 'netstat -an | findstr ":8501" | findstr LISTENING')

    sftp.close()
    ssh.close()

    print()
    print("=" * 60)
    print("  DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print()
    print(f"  Landing Page: http://3.231.147.217")
    print(f"  Dashboard:    http://3.231.147.217:8501")
    print()
    print("  Both services are set to auto-start on reboot.")
    print("=" * 60)

if __name__ == "__main__":
    main()
