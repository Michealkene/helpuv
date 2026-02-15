#!/usr/bin/env python3
"""Download trading shorts on VPS using yt-dlp with proper YouTube Shorts search"""
import paramiko
import os
import sys

VPS_IP = "185.113.249.211"
VPS_USER = "root"
VPS_PASS = "pUZ9z0m5mFK@"
LOCAL_DIR = r"C:\Users\Administrator\Desktop\Downloaded_Videos\trading_shorts"

def run(ssh, cmd, timeout=300):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print(f"  > {cmd[:150]}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    for line in out.split('\n')[-8:]:
        if line.strip():
            try:
                print(f"    {line[:200]}")
            except:
                print(f"    {line.encode('ascii', 'replace').decode()[:200]}")
    if err:
        for line in err.split('\n')[-3:]:
            if line.strip() and 'WARNING' not in line.upper() and 'hint:' not in line.lower() and 'note:' not in line.lower():
                try:
                    print(f"    [e] {line[:200]}")
                except:
                    pass
    return out

def main():
    os.makedirs(LOCAL_DIR, exist_ok=True)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print(f"Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=15)
    print("Connected!\n")

    # Verify yt-dlp
    run(ssh, "/usr/local/bin/yt-dlp --version")
    run(ssh, "mkdir -p /tmp/trading_shorts")

    # YouTube Shorts channels that post trading content (shorts-only channels)
    yt_channels = [
        ("@TheTradingChannel/shorts", "tradingchannel", 15),
        ("@TraderNick/shorts", "tradernick", 15),
        ("@FXTM/shorts", "fxtm", 10),
        ("@TradingWithRayner/shorts", "rayner", 10),
    ]

    for channel, label, count in yt_channels:
        print(f"\n=== YouTube @{label} (max {count}) ===")
        cmd = (
            f'/usr/local/bin/yt-dlp "https://www.youtube.com/{channel}" '
            f'-I 1:{count} --match-filter "duration < 61" '
            f'-o "/tmp/trading_shorts/yt_{label}_%(title).50s_%(id)s.%(ext)s" '
            f'-f "best[height<=720][ext=mp4]/best[ext=mp4]/best" '
            f'--merge-output-format mp4 --no-warnings --no-check-certificates --geo-bypass '
            f'--extractor-args "youtube:player_client=web" '
            f'2>&1 | tail -15'
        )
        run(ssh, cmd, timeout=300)

    # Also try Instagram Reels (trading accounts)
    ig_users = [
        ("forexsignals", 8),
        ("tradingview", 8),
    ]

    for user, count in ig_users:
        print(f"\n=== Instagram @{user} ===")
        cmd = (
            f'/usr/local/bin/yt-dlp "https://www.instagram.com/{user}/reels/" '
            f'-I 1:{count} --match-filter "duration < 61" '
            f'-o "/tmp/trading_shorts/ig_{user}_%(title).50s_%(id)s.%(ext)s" '
            f'-f "best[ext=mp4]/best" '
            f'--no-warnings --no-check-certificates --geo-bypass '
            f'2>&1 | tail -10'
        )
        run(ssh, cmd, timeout=120)

    # TikTok users
    tt_users = [
        ("forex_king_official", 10),
        ("thetradinggeek", 10),
        ("tradingmadeeasy", 10),
    ]

    for user, count in tt_users:
        print(f"\n=== TikTok @{user} ===")
        cmd = (
            f'/usr/local/bin/yt-dlp "https://www.tiktok.com/@{user}" '
            f'-I 1:{count} --match-filter "duration < 61" '
            f'-o "/tmp/trading_shorts/tt_{user}_%(title).50s_%(id)s.%(ext)s" '
            f'-f "best[ext=mp4]/best" '
            f'--no-warnings --no-check-certificates --geo-bypass '
            f'2>&1 | tail -10'
        )
        run(ssh, cmd, timeout=120)

    # Count
    print("\n" + "="*60)
    count_str = run(ssh, "ls /tmp/trading_shorts/*.mp4 2>/dev/null | wc -l")
    count = int(count_str.strip()) if count_str.strip().isdigit() else 0
    print(f"\nTotal: {count} videos")

    # List files with sizes
    run(ssh, "ls -lhS /tmp/trading_shorts/*.mp4 2>/dev/null | head -60")

    # Transfer
    if count > 0:
        print(f"\n=== Transferring {count} videos ===")
        sftp = ssh.open_sftp()
        remote_files = [f for f in sftp.listdir("/tmp/trading_shorts/") if f.endswith('.mp4')]
        transferred = 0
        for i, fname in enumerate(remote_files, 1):
            safe_name = "".join(c if c.isalnum() or c in '._-[] ' else '_' for c in fname)
            local_path = os.path.join(LOCAL_DIR, safe_name)
            try:
                print(f"  [{i}/{len(remote_files)}] {safe_name[:65]}")
                sftp.get(f"/tmp/trading_shorts/{fname}", local_path)
                transferred += 1
            except Exception as e:
                print(f"    Error: {e}")
        sftp.close()
        print(f"\nTransferred {transferred} files")

    run(ssh, "rm -rf /tmp/trading_shorts")
    ssh.close()

    # Count local files
    local_count = len([f for f in os.listdir(LOCAL_DIR) if f.endswith('.mp4')])
    print(f"\n{'='*60}")
    print(f"  FINAL: {local_count} trading short videos")
    print(f"  Location: {LOCAL_DIR}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
