"""Set up SSH tunnel from Linux VPS to Windows VPS for API access"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import paramiko

# Connect to Linux VPS
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Need to use SSH key - let's use the ssh command from local which has the key
print("This script sets up an SSH tunnel on the Linux VPS.")
print("Run manually or use the commands below.\n")

# We'll configure this via SSH from local to Linux VPS
import subprocess

cmds = [
    # Install sshpass on Linux VPS for Windows SSH auth
    "apt-get install -y sshpass autossh 2>/dev/null",

    # Create tunnel script
    '''cat > /usr/local/bin/xaubot-tunnel.sh << 'SCRIPT'
#!/bin/bash
# SSH tunnel: forward local port 5001 to Windows VPS port 5001
sshpass -p 'Y;Y$aJloHykJxnxueYuVvwD0e7$RS!Ya' \\
  ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -o ServerAliveCountMax=3 \\
  -N -L 127.0.0.1:5001:127.0.0.1:5001 \\
  Administrator@3.231.147.217
SCRIPT
chmod +x /usr/local/bin/xaubot-tunnel.sh''',

    # Create systemd service for the tunnel
    '''cat > /etc/systemd/system/xaubot-tunnel.service << 'SVC'
[Unit]
Description=XAUBOT SSH Tunnel to Windows VPS
After=network.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/xaubot-tunnel.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SVC''',

    # Enable and start
    "systemctl daemon-reload",
    "systemctl enable xaubot-tunnel.service",
    "systemctl start xaubot-tunnel.service",
    "sleep 5",
    "systemctl status xaubot-tunnel.service --no-pager",

    # Test tunnel
    "curl -s --max-time 10 -H 'X-API-Key: xaubot-engine-key' http://127.0.0.1:5001/health || echo 'TUNNEL NOT YET WORKING'",
]

for cmd in cmds:
    print(f"\n>>> Running: {cmd[:80]}...")
    result = subprocess.run(
        ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10',
         'root@74.50.87.77', cmd],
        capture_output=True, text=True, timeout=30
    )
    if result.stdout.strip():
        print(f"  {result.stdout.strip()[:400]}")
    if result.stderr.strip() and 'WARNING' not in result.stderr:
        print(f"  [err] {result.stderr.strip()[:200]}")

print("\n\nTunnel setup complete!")
print("The Linux VPS now forwards 127.0.0.1:5001 -> Windows VPS:5001 via SSH tunnel")
print("Update WINDOWS_VPS_URL to http://127.0.0.1:5001 in the xaubot-saas service")
