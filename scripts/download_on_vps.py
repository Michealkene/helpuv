#!/usr/bin/env python3
"""Download trading shorts on VPS and SCP them back"""
import paramiko
import os
import sys

VPS_IP = "185.113.249.211"
VPS_USER = "root"
VPS_PASS = "pUZ9z0m5mFK@"
LOCAL_DIR = r"C:\Users\Administrator\Desktop\Downloaded_Videos\trading_shorts"

def run_cmd(ssh, cmd, timeout=300):
    print(f"  > {cmd[:120]}...")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        for line in out.split('\n')[-5:]:
            print(f"    {line[:200]}")
    if err:
        for line in err.split('\n')[-3:]:
            if 'WARNING' not in line.upper():
                print(f"    [err] {line[:200]}")
    return out, err

def main():
    os.makedirs(LOCAL_DIR, exist_ok=True)

    print(f"Connecting to VPS {VPS_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=15)
    print("Connected!\n")

    # Step 1: Install yt-dlp on VPS
    print("=== Installing yt-dlp on VPS ===")
    run_cmd(ssh, "which yt-dlp || pip3 install yt-dlp || pip install yt-dlp", timeout=120)
    run_cmd(ssh, "yt-dlp --version")

    # Step 2: Create download directory on VPS
    run_cmd(ssh, "mkdir -p /tmp/trading_shorts")

    # Step 3: Download trading shorts on VPS
    searches = [
        ("forex trading tips 60 seconds shorts", 15),
        ("crypto bitcoin trading shorts tutorial", 15),
        ("day trading stock market beginner shorts", 15),
        ("trading motivation lifestyle rich shorts", 10),
        ("forex signals profit shorts", 10),
    ]

    for query, count in searches:
        print(f"\n=== Downloading: {query} ({count} videos) ===")
        cmd = (
            f'yt-dlp "ytsearch{count}:{query}" '
            f'--match-filter "duration < 61" '
            f'-o "/tmp/trading_shorts/%(title).60s_%(id)s.%(ext)s" '
            f'-f "best[height<=720][ext=mp4]/best[ext=mp4]/best" '
            f'--merge-output-format mp4 '
            f'--no-warnings --no-check-certificates --geo-bypass '
            f'--extractor-args "youtube:player_client=web" '
            f'2>&1 | tail -20'
        )
        run_cmd(ssh, cmd, timeout=300)

    # Step 4: Count downloaded files
    print("\n=== Results on VPS ===")
    out, _ = run_cmd(ssh, "ls /tmp/trading_shorts/*.mp4 2>/dev/null | wc -l")
    count = int(out.strip()) if out.strip().isdigit() else 0
    print(f"\nTotal videos on VPS: {count}")

    if count == 0:
        print("No videos downloaded on VPS either. Trying TikTok...")
        # Try TikTok on VPS
        tiktok_searches = [
            "@forex_king_official",
            "@tradingexpert",
            "@cryptotrading101",
        ]
        for user in tiktok_searches:
            cmd = (
                f'yt-dlp "https://www.tiktok.com/{user}" '
                f'-I 1:10 --match-filter "duration < 61" '
                f'-o "/tmp/trading_shorts/TT_%(title).60s_%(id)s.%(ext)s" '
                f'-f "best[ext=mp4]/best" '
                f'--no-warnings --no-check-certificates --geo-bypass '
                f'2>&1 | tail -10'
            )
            print(f"\n--- TikTok: {user} ---")
            run_cmd(ssh, cmd, timeout=120)

        out, _ = run_cmd(ssh, "ls /tmp/trading_shorts/*.mp4 2>/dev/null | wc -l")
        count = int(out.strip()) if out.strip().isdigit() else 0
        print(f"\nTotal after TikTok: {count}")

    # Step 5: List files
    print("\n=== Files ===")
    run_cmd(ssh, "ls -la /tmp/trading_shorts/*.mp4 2>/dev/null | head -60")

    # Step 6: SCP files back
    if count > 0:
        print(f"\n=== Transferring {count} files to local machine ===")
        sftp = ssh.open_sftp()
        remote_files = sftp.listdir("/tmp/trading_shorts/")
        mp4_files = [f for f in remote_files if f.endswith('.mp4')]

        for i, fname in enumerate(mp4_files, 1):
            remote_path = f"/tmp/trading_shorts/{fname}"
            local_path = os.path.join(LOCAL_DIR, fname)
            try:
                print(f"  [{i}/{len(mp4_files)}] {fname[:70]}...")
                sftp.get(remote_path, local_path)
            except Exception as e:
                print(f"    Error: {e}")

        sftp.close()
        print(f"\nTransferred {len(mp4_files)} files to {LOCAL_DIR}")

    # Cleanup
    run_cmd(ssh, "rm -rf /tmp/trading_shorts")
    ssh.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
