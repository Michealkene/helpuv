#!/usr/bin/env python3
"""Install yt-dlp on VPS, download trading shorts, transfer back"""
import paramiko
import os
import time

VPS_IP = "185.113.249.211"
VPS_USER = "root"
VPS_PASS = "pUZ9z0m5mFK@"
LOCAL_DIR = r"C:\Users\Administrator\Desktop\Downloaded_Videos\trading_shorts"

def run(ssh, cmd, timeout=300):
    print(f"  > {cmd[:150]}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    for line in out.split('\n')[-5:]:
        if line.strip():
            print(f"    {line[:200]}")
    if err:
        for line in err.split('\n')[-3:]:
            if line.strip() and 'WARNING' not in line.upper() and 'hint:' not in line.lower():
                print(f"    [e] {line[:200]}")
    return out

def main():
    os.makedirs(LOCAL_DIR, exist_ok=True)
    print(f"Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=15)
    print("Connected!\n")

    # Install yt-dlp via curl (standalone binary)
    print("=== Installing yt-dlp ===")
    run(ssh, "curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp && chmod +x /usr/local/bin/yt-dlp", timeout=60)
    run(ssh, "/usr/local/bin/yt-dlp --version")

    # Install ffmpeg if missing
    run(ssh, "which ffmpeg || apt-get install -y ffmpeg 2>/dev/null", timeout=60)

    # Create dir
    run(ssh, "mkdir -p /tmp/trading_shorts")

    # Download trading shorts - using ytsearch
    queries = [
        ("ytsearch15:forex trading tips short 60 seconds tutorial", "forex"),
        ("ytsearch15:crypto trading bitcoin short tips beginner", "crypto"),
        ("ytsearch15:stock market day trading strategy short", "stocks"),
        ("ytsearch10:trading motivation rich lifestyle short", "motivation"),
        ("ytsearch10:gold trading forex strategy short tips", "gold"),
    ]

    for search_url, label in queries:
        print(f"\n=== [{label}] Downloading ===")
        cmd = (
            f'/usr/local/bin/yt-dlp "{search_url}" '
            f'--match-filter "duration < 61" '
            f'-o "/tmp/trading_shorts/{label}_%(title).50s_%(id)s.%(ext)s" '
            f'-f "best[height<=720][ext=mp4]/best[ext=mp4]/best" '
            f'--merge-output-format mp4 '
            f'--no-warnings --no-check-certificates --geo-bypass '
        )
        run(ssh, cmd, timeout=300)

    # Also try TikTok user profiles
    tiktok_users = [
        "forex_king_official",
        "thetradinggeek",
        "daytradingfam",
        "cryptoking",
    ]

    for user in tiktok_users:
        print(f"\n=== TikTok @{user} ===")
        cmd = (
            f'/usr/local/bin/yt-dlp "https://www.tiktok.com/@{user}" '
            f'-I 1:10 --match-filter "duration < 61" '
            f'-o "/tmp/trading_shorts/tt_{user}_%(title).50s_%(id)s.%(ext)s" '
            f'-f "best[ext=mp4]/best" '
            f'--no-warnings --no-check-certificates --geo-bypass '
        )
        run(ssh, cmd, timeout=120)

    # Count results
    print("\n" + "="*60)
    count_str = run(ssh, "ls /tmp/trading_shorts/*.mp4 2>/dev/null | wc -l")
    count = int(count_str.strip()) if count_str.strip().isdigit() else 0
    print(f"\nTotal videos downloaded: {count}")

    # List files
    run(ssh, "ls -lhS /tmp/trading_shorts/*.mp4 2>/dev/null | head -60")

    # Transfer files
    if count > 0:
        print(f"\n=== Transferring {count} videos to local machine ===")
        sftp = ssh.open_sftp()
        remote_files = [f for f in sftp.listdir("/tmp/trading_shorts/") if f.endswith('.mp4')]
        transferred = 0
        for i, fname in enumerate(remote_files, 1):
            remote_path = f"/tmp/trading_shorts/{fname}"
            # Clean filename for Windows
            safe_name = fname.replace('/', '_').replace('\\', '_').replace(':', '_').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')
            local_path = os.path.join(LOCAL_DIR, safe_name)
            try:
                print(f"  [{i}/{len(remote_files)}] {safe_name[:60]}...")
                sftp.get(remote_path, local_path)
                transferred += 1
            except Exception as e:
                print(f"    Error: {e}")
        sftp.close()
        print(f"\nTransferred {transferred} files to {LOCAL_DIR}")
    else:
        print("No videos to transfer.")

    # Cleanup VPS
    run(ssh, "rm -rf /tmp/trading_shorts")
    ssh.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
