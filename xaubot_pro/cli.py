#!/usr/bin/env python3
"""
Viral TikTok Bot - Command Line Interface
For advanced users who prefer terminal over GUI
"""

import argparse
import json
import sys
from viral_bot import (
    ConfigManager, RedditScraper, VideoProcessor, 
    TikTokUploader, DOWNLOADS_DIR, PROCESSED_DIR
)
import os


def cmd_add_account(args):
    """Add new TikTok account"""
    accounts = ConfigManager.load_accounts()
    
    account = {
        'name': args.name,
        'added': datetime.now().isoformat(),
        'videos_posted': 0
    }
    
    accounts.append(account)
    ConfigManager.save_accounts(accounts)
    print(f"✅ Account '{args.name}' added successfully!")


def cmd_list_accounts(args):
    """List all accounts"""
    accounts = ConfigManager.load_accounts()
    
    if not accounts:
        print("No accounts found. Add one with: --add-account")
        return
    
    print("\n📱 TikTok Accounts:")
    print("-" * 60)
    for i, acc in enumerate(accounts, 1):
        print(f"{i}. {acc['name']}")
        print(f"   Videos posted: {acc['videos_posted']}")
        print(f"   Added: {acc['added']}")
        print()


def cmd_scrape(args):
    """Scrape viral videos"""
    config = ConfigManager.load_config()
    subreddits = args.subreddits or config['reddit_subreddits']
    min_upvotes = args.min_upvotes or config['min_upvotes']
    
    print(f"\n🔍 Scraping from: {', '.join(subreddits)}")
    print(f"   Min upvotes: {min_upvotes}")
    print()
    
    all_videos = []
    
    for sub in subreddits:
        print(f"Checking r/{sub}...", end=" ")
        videos = RedditScraper.get_viral_videos(sub, limit=args.limit, min_upvotes=min_upvotes)
        all_videos.extend(videos)
        print(f"✓ Found {len(videos)} videos")
    
    if not all_videos:
        print("\n❌ No videos found. Try lowering min_upvotes or different subreddits.")
        return
    
    print(f"\n📊 Total videos found: {len(all_videos)}")
    print("\nTop 10 by upvotes:")
    print("-" * 80)
    
    sorted_videos = sorted(all_videos, key=lambda x: x['upvotes'], reverse=True)[:10]
    
    for i, video in enumerate(sorted_videos, 1):
        print(f"{i}. [{video['upvotes']:,} upvotes] {video['title'][:60]}")
        print(f"   r/{video['subreddit']} - {video['url']}")
        print()
    
    # Save to file
    output_file = "scraped_videos.json"
    with open(output_file, 'w') as f:
        json.dump(all_videos, f, indent=2)
    
    print(f"💾 Saved all {len(all_videos)} videos to: {output_file}")


def cmd_download(args):
    """Download video"""
    print(f"\n⬇️  Downloading: {args.url}")
    
    video_path = VideoProcessor.download_video(args.url)
    
    if video_path:
        print(f"✅ Downloaded to: {video_path}")
    else:
        print("❌ Download failed")
        sys.exit(1)


def cmd_transform(args):
    """Transform video for TikTok"""
    print(f"\n🎬 Transforming: {args.input}")
    
    output = args.output or os.path.join(PROCESSED_DIR, f"tiktok_{int(time.time())}.mp4")
    
    config = {
        'resize': True,
        'speed_change': args.speed or 1.05
    }
    
    success = VideoProcessor.transform_for_tiktok(args.input, output, config)
    
    if success:
        print(f"✅ Transformed video saved to: {output}")
    else:
        print("❌ Transform failed")
        sys.exit(1)


def cmd_upload(args):
    """Upload video to TikTok"""
    print(f"\n📤 Uploading: {args.video}")
    print(f"   Account: {args.account}")
    print(f"   Caption: {args.caption}")
    
    success = TikTokUploader.upload_video(args.video, args.caption, args.account)
    
    if success:
        print("✅ Upload successful!")
        
        # Update account stats
        accounts = ConfigManager.load_accounts()
        for acc in accounts:
            if acc['name'] == args.account:
                acc['videos_posted'] += 1
        ConfigManager.save_accounts(accounts)
    else:
        print("❌ Upload failed")
        sys.exit(1)


def cmd_pipeline(args):
    """Run complete pipeline: scrape → download → transform → upload"""
    print("\n🚀 Running complete pipeline...")
    print("=" * 60)
    
    # 1. Scrape
    print("\n[1/4] Scraping viral videos...")
    config = ConfigManager.load_config()
    videos = []
    
    for sub in config['reddit_subreddits']:
        vids = RedditScraper.get_viral_videos(sub, limit=3, min_upvotes=config['min_upvotes'])
        videos.extend(vids)
    
    if not videos:
        print("❌ No videos found")
        return
    
    print(f"✓ Found {len(videos)} videos")
    
    # 2. Process each video
    accounts = ConfigManager.load_accounts()
    if not accounts:
        print("❌ No accounts configured")
        return
    
    import random
    
    for i, video in enumerate(videos[:args.count], 1):
        print(f"\n[Video {i}/{min(len(videos), args.count)}]")
        print("=" * 60)
        
        # Download
        print("⬇️  Downloading...")
        video_path = VideoProcessor.download_video(video['url'])
        if not video_path:
            print("❌ Download failed, skipping")
            continue
        print(f"✓ Downloaded")
        
        # Transform
        print("🎬 Transforming...")
        output_path = os.path.join(PROCESSED_DIR, f"tiktok_{int(time.time())}.mp4")
        transform_config = config['video_transformation']
        success = VideoProcessor.transform_for_tiktok(video_path, output_path, transform_config)
        if not success:
            print("❌ Transform failed, skipping")
            continue
        print(f"✓ Transformed")
        
        # Upload
        account = random.choice(accounts)
        print(f"📤 Uploading to: {account['name']}")
        caption = f"{video['title'][:80]} 🔥 #fyp #viral"
        success = TikTokUploader.upload_video(output_path, caption, account['name'])
        
        if success:
            print("✅ Upload successful!")
            account['videos_posted'] += 1
        else:
            print("❌ Upload failed")
        
        # Cleanup
        try:
            os.remove(video_path)
        except:
            pass
    
    # Save updated account stats
    ConfigManager.save_accounts(accounts)
    
    print("\n✅ Pipeline complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Viral TikTok Bot - CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List accounts
  python cli.py accounts list
  
  # Add account
  python cli.py accounts add --name "MyAccount"
  
  # Scrape videos
  python cli.py scrape --subreddits TikTokCringe Unexpected --min-upvotes 1000
  
  # Download video
  python cli.py download --url "https://www.reddit.com/r/videos/..."
  
  # Transform video
  python cli.py transform --input video.mp4 --output tiktok.mp4 --speed 1.05
  
  # Upload video
  python cli.py upload --video tiktok.mp4 --account "MyAccount" --caption "Check this out!"
  
  # Run full pipeline (scrape, download, transform, upload)
  python cli.py pipeline --count 5
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Accounts commands
    accounts_parser = subparsers.add_parser('accounts', help='Manage TikTok accounts')
    accounts_sub = accounts_parser.add_subparsers(dest='accounts_command')
    
    accounts_list = accounts_sub.add_parser('list', help='List all accounts')
    
    accounts_add = accounts_sub.add_parser('add', help='Add new account')
    accounts_add.add_argument('--name', required=True, help='Account name/username')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape viral videos')
    scrape_parser.add_argument('--subreddits', nargs='+', help='Subreddits to scrape')
    scrape_parser.add_argument('--min-upvotes', type=int, help='Minimum upvotes')
    scrape_parser.add_argument('--limit', type=int, default=10, help='Videos per subreddit')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download video')
    download_parser.add_argument('--url', required=True, help='Video URL')
    
    # Transform command
    transform_parser = subparsers.add_parser('transform', help='Transform video')
    transform_parser.add_argument('--input', required=True, help='Input video file')
    transform_parser.add_argument('--output', help='Output video file')
    transform_parser.add_argument('--speed', type=float, help='Speed multiplier (e.g., 1.05)')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload to TikTok')
    upload_parser.add_argument('--video', required=True, help='Video file to upload')
    upload_parser.add_argument('--account', required=True, help='TikTok account name')
    upload_parser.add_argument('--caption', required=True, help='Video caption')
    
    # Pipeline command
    pipeline_parser = subparsers.add_parser('pipeline', help='Run complete pipeline')
    pipeline_parser.add_argument('--count', type=int, default=5, help='Number of videos to process')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Route to appropriate function
    if args.command == 'accounts':
        if args.accounts_command == 'list':
            cmd_list_accounts(args)
        elif args.accounts_command == 'add':
            cmd_add_account(args)
        else:
            accounts_parser.print_help()
    
    elif args.command == 'scrape':
        cmd_scrape(args)
    
    elif args.command == 'download':
        cmd_download(args)
    
    elif args.command == 'transform':
        cmd_transform(args)
    
    elif args.command == 'upload':
        cmd_upload(args)
    
    elif args.command == 'pipeline':
        cmd_pipeline(args)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    import time
    from datetime import datetime
    main()
