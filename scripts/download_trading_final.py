#!/usr/bin/env python3
"""Download trading shorts using Invidious API (YouTube mirror) + TikTok via VPS"""
import paramiko
import requests
import os
import subprocess
import json
import time
import sys

VPS_IP = "185.113.249.211"
VPS_USER = "root"
VPS_PASS = "pUZ9z0m5mFK@"
LOCAL_DIR = r"C:\Users\Administrator\Desktop\Downloaded_Videos\trading_shorts"
PROXY = "socks5://127.0.0.1:1080"

os.makedirs(LOCAL_DIR, exist_ok=True)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def download_via_invidious(query, max_results=20, label=""):
    """Use Invidious API to search and get direct video URLs"""
    # Multiple Invidious instances
    instances = [
        "https://vid.puffyan.us",
        "https://invidious.fdn.fr",
        "https://inv.nadeko.net",
        "https://invidious.nerdvpn.de",
        "https://inv.tux.pizza",
    ]

    videos_found = []

    for instance in instances:
        try:
            print(f"  Trying {instance}...")
            url = f"{instance}/api/v1/search?q={query}&type=video&sort_by=relevance&features=short"
            resp = requests.get(url, timeout=15, proxies={"https": PROXY, "http": PROXY})
            if resp.status_code == 200:
                results = resp.json()
                for vid in results:
                    duration = vid.get("lengthSeconds", 999)
                    if duration <= 60:
                        videos_found.append({
                            "id": vid["videoId"],
                            "title": vid.get("title", "untitled"),
                            "duration": duration,
                            "instance": instance,
                        })
                        if len(videos_found) >= max_results:
                            break
                if videos_found:
                    print(f"    Found {len(videos_found)} short videos")
                    break
        except Exception as e:
            print(f"    Error: {e}")
            continue

    # Download each video via Invidious direct link
    downloaded = []
    for i, vid in enumerate(videos_found, 1):
        vid_id = vid["id"]
        title = "".join(c if c.isalnum() or c in ' _-' else '_' for c in vid["title"])[:50]
        fname = f"{label}_{title}_{vid_id}.mp4"
        fpath = os.path.join(LOCAL_DIR, fname)

        if os.path.exists(fpath):
            print(f"  [{i}/{len(videos_found)}] Already exists: {fname[:60]}")
            downloaded.append(fpath)
            continue

        # Try to get direct download URL from Invidious
        try:
            api_url = f"{vid['instance']}/api/v1/videos/{vid_id}"
            resp = requests.get(api_url, timeout=15, proxies={"https": PROXY, "http": PROXY})
            if resp.status_code == 200:
                data = resp.json()
                # Get best format URL
                formats = data.get("formatStreams", []) + data.get("adaptiveFormats", [])
                mp4_url = None
                for fmt in formats:
                    if fmt.get("container") == "mp4" and fmt.get("type", "").startswith("video/"):
                        if fmt.get("qualityLabel", "") in ["720p", "480p", "360p"]:
                            mp4_url = fmt.get("url")
                            break
                if not mp4_url:
                    # Fallback: any format
                    for fmt in data.get("formatStreams", []):
                        mp4_url = fmt.get("url")
                        break

                if mp4_url:
                    print(f"  [{i}/{len(videos_found)}] Downloading: {title[:50]}...")
                    video_resp = requests.get(mp4_url, timeout=60, stream=True,
                                             proxies={"https": PROXY, "http": PROXY})
                    if video_resp.status_code == 200:
                        with open(fpath, 'wb') as f:
                            for chunk in video_resp.iter_content(chunk_size=1024*1024):
                                f.write(chunk)
                        size_mb = os.path.getsize(fpath) / (1024*1024)
                        print(f"    OK ({size_mb:.1f} MB)")
                        downloaded.append(fpath)
                    else:
                        print(f"    Download failed: HTTP {video_resp.status_code}")
                else:
                    print(f"    No MP4 format found")
        except Exception as e:
            print(f"    Error: {e}")

    return downloaded


def download_tiktok_on_vps(users_and_counts):
    """Download TikTok videos on VPS and SCP them back"""
    print("\n=== Downloading TikTok on VPS ===")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=15)

    ssh.exec_command("mkdir -p /tmp/tt_trading")

    downloaded = []
    for user, count in users_and_counts:
        print(f"\n  TikTok @{user} (max {count})...")
        cmd = (
            f'/usr/local/bin/yt-dlp "https://www.tiktok.com/@{user}" '
            f'-I 1:{count} --match-filter "duration < 61" '
            f'-o "/tmp/tt_trading/tt_{user}_%(title).40s_%(id)s.%(ext)s" '
            f'-f "best[ext=mp4]/best" '
            f'--no-warnings --no-check-certificates --geo-bypass '
        )
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=180)
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        for line in (out + err).split('\n')[-5:]:
            if line.strip():
                try:
                    print(f"    {line.strip()[:150]}")
                except:
                    pass

    # Count and transfer
    stdin, stdout, stderr = ssh.exec_command("ls /tmp/tt_trading/*.mp4 2>/dev/null")
    files = stdout.read().decode('utf-8', errors='replace').strip().split('\n')
    files = [f for f in files if f.strip() and f.endswith('.mp4')]

    if files:
        print(f"\n  Transferring {len(files)} TikTok videos...")
        sftp = ssh.open_sftp()
        for f in files:
            fname = os.path.basename(f)
            safe_name = "".join(c if c.isalnum() or c in '._-[] ' else '_' for c in fname)
            local_path = os.path.join(LOCAL_DIR, safe_name)
            try:
                sftp.get(f.strip(), local_path)
                downloaded.append(local_path)
                print(f"    OK: {safe_name[:60]}")
            except:
                pass
        sftp.close()

    ssh.exec_command("rm -rf /tmp/tt_trading")
    ssh.close()
    return downloaded


def main():
    all_downloaded = []

    # Part 1: YouTube via Invidious API
    searches = [
        ("forex trading tips", 12, "forex"),
        ("crypto trading shorts", 12, "crypto"),
        ("stock market trading strategy", 10, "stocks"),
        ("day trading beginner", 8, "daytrade"),
        ("trading motivation rich", 8, "motivation"),
        ("gold trading forex", 5, "gold"),
        ("trading lifestyle", 5, "lifestyle"),
    ]

    for query, count, label in searches:
        print(f"\n{'='*50}")
        print(f"  YouTube Search: {query} (max {count})")
        print(f"{'='*50}")
        results = download_via_invidious(query, max_results=count, label=label)
        all_downloaded.extend(results)
        print(f"  Got {len(results)} videos (total: {len(all_downloaded)})")

        if len(all_downloaded) >= 50:
            break

    # Part 2: TikTok via VPS
    if len(all_downloaded) < 50:
        remaining = 50 - len(all_downloaded)
        tiktok_users = [
            ("tradingmadeeasy", min(remaining, 10)),
            ("forextrader_daily", min(remaining, 10)),
            ("tiktoktrading", min(remaining, 10)),
            ("daytradingtips", min(remaining, 10)),
            ("tradingwithkhalid", min(remaining, 10)),
        ]
        tt_results = download_tiktok_on_vps(tiktok_users)
        all_downloaded.extend(tt_results)

    # Final count
    local_mp4s = [f for f in os.listdir(LOCAL_DIR) if f.endswith('.mp4')]
    print(f"\n{'='*60}")
    print(f"  FINAL RESULTS")
    print(f"{'='*60}")
    print(f"  Total: {len(local_mp4s)} trading short videos (<60s)")
    print(f"  Location: {LOCAL_DIR}")
    total_size = sum(os.path.getsize(os.path.join(LOCAL_DIR, f)) for f in local_mp4s)
    print(f"  Total size: {total_size / (1024*1024):.1f} MB")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
