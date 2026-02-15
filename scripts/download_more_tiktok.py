#!/usr/bin/env python3
"""Download more TikTok trading videos on VPS"""
import paramiko
import os
import sys

VPS_IP = "185.113.249.211"
VPS_USER = "root"
VPS_PASS = "pUZ9z0m5mFK@"
LOCAL_DIR = r"C:\Users\Administrator\Desktop\Downloaded_Videos\trading_shorts"

os.makedirs(LOCAL_DIR, exist_ok=True)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=15)
    print("Connected to VPS\n")

    ssh.exec_command("mkdir -p /tmp/tt_more")

    # More TikTok trading users to try
    users = [
        "cryptoking", "theforexguy", "tradingcoach", "fxlifestyle",
        "tradermindset", "stocktips", "wallstreetbets", "investingtips",
        "tradinglife", "forexmentor", "bitcointrader", "stockmarket",
        "tradingsecrets", "forexeducation", "tradingpsychology",
        "investordaily", "stocktrading", "cryptotrader", "wealthbuilder",
        "traderlifestyle", "forexsignals", "marketanalysis", "scalping",
        "swingtrading", "optionstrading", "financialfreedom", "passiveincome",
        "moneymindset", "wealthcreation", "stockpicks",
    ]

    total = 0
    for user in users:
        if total >= 40:  # We already have 18, need ~32 more
            break
        print(f"TikTok @{user}...", end=" ", flush=True)
        cmd = (
            f'/usr/local/bin/yt-dlp "https://www.tiktok.com/@{user}" '
            f'-I 1:8 --match-filter "duration < 61" '
            f'-o "/tmp/tt_more/tt_{user}_%(title).40s_%(id)s.%(ext)s" '
            f'-f "best[ext=mp4]/best" '
            f'--no-warnings --no-check-certificates --geo-bypass '
            f'2>&1'
        )
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
        out = stdout.read().decode('utf-8', errors='replace')

        # Count new mp4s
        stdin2, stdout2, _ = ssh.exec_command(f"ls /tmp/tt_more/tt_{user}_*.mp4 2>/dev/null | wc -l")
        count = stdout2.read().decode().strip()
        count = int(count) if count.isdigit() else 0
        total += count

        if count > 0:
            print(f"{count} videos (total: {total})")
        else:
            # Check error
            if "private" in out.lower() or "private" in stderr.read().decode('utf-8', errors='replace').lower():
                print("private")
            elif "does not have" in out.lower():
                print("no videos")
            elif "Unable to extract" in out:
                print("extract error")
            else:
                print("0")

    # Transfer all
    stdin, stdout, _ = ssh.exec_command("ls /tmp/tt_more/*.mp4 2>/dev/null")
    files = [f.strip() for f in stdout.read().decode('utf-8', errors='replace').strip().split('\n') if f.strip().endswith('.mp4')]

    print(f"\nTransferring {len(files)} files...")
    sftp = ssh.open_sftp()
    transferred = 0
    for f in files:
        fname = os.path.basename(f)
        safe_name = "".join(c if c.isalnum() or c in '._-[] ' else '_' for c in fname)
        local_path = os.path.join(LOCAL_DIR, safe_name)
        if not os.path.exists(local_path):
            try:
                sftp.get(f, local_path)
                transferred += 1
            except:
                pass
    sftp.close()
    print(f"Transferred {transferred} new files")

    ssh.exec_command("rm -rf /tmp/tt_more")
    ssh.close()

    local_count = len([f for f in os.listdir(LOCAL_DIR) if f.endswith('.mp4')])
    total_size = sum(os.path.getsize(os.path.join(LOCAL_DIR, f)) for f in os.listdir(LOCAL_DIR) if f.endswith('.mp4'))
    print(f"\n{'='*50}")
    print(f"  Total local: {local_count} videos ({total_size/(1024*1024):.1f} MB)")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
